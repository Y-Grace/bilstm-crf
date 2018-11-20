__author__ = 'jmh081701'
import  numpy as np
import  random
import json
import  copy
class DATA_PREPROCESS:
    def __init__(self,train_data,train_label,test_data,test_label,embedded_words,vocb,seperate_rate=0.1,sequenct_length=100,state={'O','B-LOC','I-LOC','B-PER','I-PER'}):
        self.train_data_file = train_data
        self.train_label_file = train_label
        self.test_data_file = test_data
        self.test_label_file = test_label
        self.word2vec_file = embedded_words
        self.vocb_file = vocb

        # 载入词向量
        self.word2vec=np.load(self.word2vec_file)
        self.embedding_vec_length = len(self.word2vec[0])

        with open(self.vocb_file,encoding='utf8') as fp:
            self.index2word = json.load(fp)

        self.words={}
        for key in self.index2word:
            word=self.index2word[key]
            self.words.setdefault(word,key)

        #处理隐状态
        self.state={}
        if state != None:
            self.state={'O':0}
            state.remove('O')
            for each in state :
                self.state.setdefault(each,len(self.state))

        #设置训练的句子长度
        self.sequence_length = sequenct_length

        #载入训练集

        with open(self.train_data_file,encoding='utf8') as fp:
            train_raw_data = fp.readlines()
            train_lines =[]
            for line in train_raw_data:
                raw_words = line.split(" ")
                if len(raw_words) > sequenct_length:
                    raw_words = raw_words[0:sequenct_length]
                words = [self.word2index(word) for word in raw_words ]
                train_lines.append(words)
                #if len(words) > self.sequence_length :
                #    self.sequence_length = len(words)
            self.train_data = copy.deepcopy(train_lines)
        print(len(self.train_data))

        with open(self.train_label_file,encoding='utf8') as fp:
            train_raw_label = fp.readlines()
            train_labels =[]
            for line in train_raw_label:
                raw_labels = line.split(" ")
                if len(raw_labels) > sequenct_length:
                    raw_labels = raw_labels[0:sequenct_length]
                if self.state != None:
                    labels = [self.state.get(label,self.state['O']) for label in raw_labels]
                else:
                    labels=[]
                    for label in raw_labels:
                        if label in self.state:
                            labels.append( self.state[label])
                        else:
                            self.state.setdefault(label,len(self.state))
                            labels.append(self.state[label])
                train_labels.append(labels)
            self.train_labels =copy.deepcopy(train_labels)
        print(len(self.train_data),len(self.train_labels))
        assert len(self.train_data)==len(self.train_labels)
        #得到state的数量
        self.state_nums = len(self.state)

        #划分训练集为 训练集和验证集
        self.train_set=set()
        self.valid_set=set()

        while len( self.valid_set ) < int(seperate_rate * len(self.train_data)):
            index = random.randint(0,len(self.train_data)-1)
            self.valid_set.add(index)
        assert len(self.train_data)==len(self.train_labels)
        #载入测试集
        with open(self.test_data_file,encoding='utf8') as fp:
            test_raw_data = fp.readlines()
            test_lines =[]
            for line in test_raw_data:
                raw_words = line.split(" ")
                words = [self.word2index(word) for word in raw_words ]
                test_lines.append(words)
                #if len(words) > self.sequence_length :
                #    self.sequence_length = len(words)
            self.test_lines =copy.deepcopy( test_lines)
        assert len(self.train_data)==len(self.train_labels)
        with open(self.test_label_file,encoding='utf8') as fp:
            test_raw_label = fp.readlines()
            test_labels =[]
            for line in test_raw_label:
                raw_labels = line.split(" ")
                labels = [self.state.get(label,self.state['O']) for label in raw_labels]
                test_lines.append(labels)
            self.test_labels = copy.deepcopy(test_labels)
        assert len(self.train_data)==len(self.train_labels)

    def word2index(self,word):
        return self.words.get(word,self.words['<UNK>'])
    def lookup(self,word):
        return self.word2vec(self.word2index(word))

    def next_train_batch(self,batch_size):
        x=[]
        y=[]
        seq_lengths=[]

        while len(x) < batch_size:
            index = random.randint(0,len(self.train_data)-2)
            if not index in self.valid_set:
                try:
                    #print({"index":index,"len(self.train_labels":len(self.train_labels),"train_data":len(self.train_data)})
                    _label = ( self.train_labels[index]+ np.zeros(shape=[self.sequence_length]).tolist() )[:self.sequence_length]
                except:
                    print({"index":index,"len(self.train_labels":len(self.train_labels),"train_data":len(self.train_data)})
                    raise  "Data Error"
                _x = self.train_data[index]
                __x=[]
                for i in range(len(_x)):
                    __x +=(self.word2vec[ int(_x[i]) ].tolist())
                __x=__x + np.zeros(shape=[self.sequence_length * self.embedding_vec_length-len(__x)]).tolist()
                x.append(np.array(__x))
                y.append(_label)
                seq_lengths.append(self.sequence_length)
        x=np.reshape(x,newshape=[-1])
        return np.float32(x),np.int32(y),np.int32(seq_lengths)

    def next_valid_batch(self,batch_size):
        x=[]
        y=[]
        seq_lengths = []
        while len(x) < batch_size:
            index = random.randint(0,len(self.valid_set)-2)
            if index in self.valid_set:
                _label = ( np.array(self.train_labels[index]).tolist()+np.zeros(shape=[self.sequence_length]).tolist() )[:self.sequence_length]
                _x=self.train_data[index]
                __x=[]
                for i in range(len(_x)):
                    __x +=(self.word2vec[ int(_x[i]) ].tolist())
                __x=__x + np.zeros(shape=[self.sequence_length * self.embedding_vec_length-len(__x)]).tolist()
                x.append(np.array(__x))
                y.append(_label)
                seq_lengths.append(self.sequence_length)
        x=np.reshape(x,newshape=[-1])
        return np.float32(x),np.int32(y),np.int32(seq_lengths)

    def test(self):
        x=[]
        y=[]
        seq_lengths=[]
        for index in range(len(self.test_lines)):
                _label = ( np.array(self.test_labels[index]).tolist()+np.zeros(shape=[self.sequence_length]).tolist())[:self.sequence_length]
                _x=self.test_lines[index]
                __x=[]
                for i in range(len(_x)):
                    __x +=(self.word2vec[ int(_x[i]) ].tolist())
                __x=__x + np.zeros(shape=[self.sequence_length * self.embedding_vec_length-len(__x)]).tolist()
                x.append(np.array(__x))
                y.append(_label)
                seq_lengths.append(self.sequence_length)
        x=np.reshape(x,newshape=[-1])
        return np.float32(x),np.int32(y),np.int32(seq_lengths)
if __name__ == '__main__':
    data=DATA_PREPROCESS(train_data="data/source_data.txt",train_label="data/source_label.txt",
                         test_data="data/tes_datat.txt",test_label="data/test_label.txt",
                         embedded_words="data/source_data.txt.ebd.npy",
                         vocb="data/source_data.txt.vab")
    x,y,_=data.next_train_batch(batch_size=2)
    print(x)
    print(y)

