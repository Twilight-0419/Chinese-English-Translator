import torch
import jieba
import torch.nn as nn
import torch.nn.functional as F
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

device=torch.device("cuda" if torch.cuda.is_available() else "cpu")

word2index_and_word_count = torch.load(ROOT / 'models' / 'word2index_and_word_count.pt')
chinese_word2index = word2index_and_word_count['chinese_word2index']
english_word2index = word2index_and_word_count['english_word2index']
chinese_word_count = word2index_and_word_count['chinese_word_count']
english_word_count = word2index_and_word_count['english_word_count']
english_index2word = {v: k for k, v in english_word2index.items()}

PAD_token=0
SOS_token=1
EOS_token=2
UNK_token=3

class C2E_Translator_Encoder(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers=1):
        super(C2E_Translator_Encoder,self).__init__()
        self.input_size=input_size
        self.hidden_size=hidden_size
        self.num_layers=num_layers
        self.embedding=nn.Embedding(input_size,hidden_size)
        self.gru=nn.GRU(hidden_size,hidden_size,num_layers,batch_first=True)

    def forward(self,x,hidden,length):
        embedded=self.embedding(x)
        output,hidden=self.gru(embedded,hidden)
        lengths=torch.tensor(length, dtype=torch.long, device=output.device)
        batch_idx=torch.arange(output.size(0), device=output.device)
        real_last=output[batch_idx,lengths-1,:]
        hidden=real_last.unsqueeze(0)
        return output,hidden

    def init_hidden(self,batch_size):
        return torch.zeros(self.num_layers,batch_size,self.hidden_size,device=device)

class C2E_Translator_Decoder_Attention(nn.Module):
    def __init__(self,hidden_size,output_size,num_layers=1):
        super(C2E_Translator_Decoder_Attention,self).__init__()
        self.hidden_size=hidden_size
        self.output_size=output_size
        self.num_layers=num_layers
        self.embedding=nn.Embedding(output_size,hidden_size)
        self.query_combine=nn.Linear(hidden_size*2,hidden_size)
        self.attn_combine=nn.Linear(hidden_size*2,hidden_size)
        self.gru=nn.GRU(hidden_size,hidden_size,num_layers,batch_first=True)
        self.out=nn.Linear(hidden_size,output_size)
        self.dropout=nn.Dropout(0.1)

    def forward(self,input,hidden,encoder_outputs,mask):
        embedded=self.embedding(input)
        embedded=self.dropout(embedded)
        query=self.query_combine(torch.cat((embedded,hidden[-1].unsqueeze(1)),dim=-1))
        permuted_encoder_outputs=encoder_outputs.permute(0,2,1)
        attn_weights=torch.bmm(query,permuted_encoder_outputs)
        attn_weights=attn_weights.masked_fill(mask.unsqueeze(1)==0,float('-inf'))
        attn_weights=F.softmax(attn_weights,dim=-1)
        attn_applied=torch.bmm(attn_weights,encoder_outputs)
        attn_combined=self.attn_combine(torch.cat((query,attn_applied),dim=-1))
        attn_combined=F.relu(attn_combined)
        output,hidden=self.gru(attn_combined,hidden)
        output=self.out(output)
        return output,hidden,attn_weights

    def init_hidden(self,batch_size):
        return torch.zeros(self.num_layers,batch_size,self.hidden_size,device=device)

encoder=C2E_Translator_Encoder(input_size=chinese_word_count,hidden_size=256,num_layers=1).to(device)
decoder=C2E_Translator_Decoder_Attention(hidden_size=256,output_size=english_word_count,num_layers=1).to(device)

encoder.load_state_dict(torch.load(ROOT / 'models' / 'encoder.pt', map_location=device))
decoder.load_state_dict(torch.load(ROOT / 'models' / 'decoder.pt', map_location=device))

def translate(zh_sentence,top_k=1,repetition_penalty=2.0):
    encoder.eval()
    decoder.eval()

    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")

    input_tensor = torch.tensor([chinese_word2index.get(word, UNK_token) for word in jieba.lcut(zh_sentence)] + [EOS_token], dtype=torch.long).unsqueeze(0).to(device)
    encoder_hidden = encoder.init_hidden(1)
    mask = (input_tensor != PAD_token).to(device)

    with torch.no_grad():
        encoder_outputs, encoder_hidden = encoder(input_tensor, encoder_hidden, [input_tensor.size(1)])
        decoder_input = torch.tensor([[SOS_token]], dtype=torch.long).to(device)
        decoder_hidden = encoder_hidden

        translated_words = []
        generated = set()
        for _ in range(50):
            decoder_output, decoder_hidden, decoder_attention = decoder(decoder_input, decoder_hidden, encoder_outputs, mask)
            logits = decoder_output.clone()
            if generated:
                seen = torch.tensor(list(generated), device=logits.device)
                logits[..., seen] = logits[..., seen] / repetition_penalty
            topv, topi = logits.topk(top_k)
            probabilities = F.softmax(topv, dim=-1)
            chosen_index = torch.multinomial(probabilities.squeeze(1), 1).item()
            next_word_index = topi.squeeze(1)[0][chosen_index].item()
            if next_word_index == EOS_token:
                break
            generated.add(next_word_index)
            translated_words.append(english_index2word.get(next_word_index, 'UNK'))
            decoder_input =torch.tensor([[next_word_index]], dtype=torch.long).to(device)

    return ' '.join(translated_words)
