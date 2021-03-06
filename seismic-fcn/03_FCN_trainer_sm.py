
# coding: utf-8

# Experimento 4
# =============
# Script para treinamento da rede LeNet5 para identificar apices de difracao.
# 
# Neste experimento sao usados 2 classes: apices e .
# 
# ---

# In[1]:

from __future__ import print_function
import numpy as np
import pymei as pm
import matplotlib as plt
import time
import os
import sys

from sklearn.utils import resample, shuffle
from FCN_utils import *
import argparse

# Importa bibliotecas proprias
#from network import run_training
from utils import *

# Configura o matplolib para plotar inline
#%matplotlib qt5
#%matplotlib notebook
import keras
from keras.models import Model, Sequential
from keras.layers import Dense, Activation, Dropout, Conv2D, MaxPooling2D, Flatten, Input
from keras import optimizers, regularizers
from keras.callbacks import ModelCheckpoint

import subprocess
import shlex

# In[2]:


# Definicao de Parametros
dataset_name = 'Solimoes' + 'Tacutu'

image_size = 64
iteration = 9

# -----------------------
# Inserção para adicionar os dados provenientes do S3
# -----------------------

#from boto.s3.connection import S3Connection

import boto3
import botocore

BUCKET_NAME = 'cloudml-fcn-sagemaker' # replace with your bucket name
KEY = 'fcn_sagemaker/train/train_SolimoesTacutu_64x64.pickle' # replace with your object key

s3 = boto3.resource('s3')
'''
try:
    s3.Bucket(BUCKET_NAME).download_file(KEY, 'train_SolimoesTacutu_64x64.pickle')
except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == "404":
        print("The object does not exist.")
    else:
        raise

KEY = 'fcn_sagemaker/validation/valid_SolimoesTacutu_64x64.pickle'
try:
    s3.Bucket(BUCKET_NAME).download_file(KEY, 'valid_SolimoesTacutu_64x64.pickle')
except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == "404":
        print("The object does not exist.")
    else:
        raise
'''
#conn = S3Connection('AKIAWOUVJOGDZT2TZJZC','/Y8VC9fZwoes/XWX2nH6ey8Syh2YiUG85nmuO8h4')
#bucket = conn.get_bucket('cloudml-fcn-sagemaker')
#for key in bucket.list():
#    try:
#        res = key.get_contents_to_filename(key.name)
#    except:
#        logging.info(key.name+":"+"FAILED")

#import t4
#t4.Package.install("fcn_sagemaker", registry="s3://cloudml-fcn-sagemaker", dest=".")

# ---
# Importacao dos Conjutos de Treino e Validacao
# ----------------------------
# 
# Importa os conjuntos gerados pelos script 'generate_data' e combina em um so conjunto de treino e validacao
# 
# ---

# In[3]:

# Carrega conjunto de treino
data_path = "/opt/ml/input/data/train"
pickle_train_data = os.path.join(data_path, 'train/train_' + dataset_name + '_64x64.pickle')
train_data = load_pickle(pickle_train_data)
train_dataset = train_data['train_dataset']
train_labels = train_data['train_labels']
print("Conjunto de treinamento:", train_dataset.shape)
print("")

# Carrega conjunto de validacao
pickle_valid_data = os.path.join(data_path, 'validation/valid_' + dataset_name + '_64x64.pickle')
valid_data = load_pickle(pickle_valid_data)

valid_dataset = valid_data['valid_dataset']
valid_labels = valid_data['valid_labels']
print("Conjunto de validacao:", valid_dataset.shape)

# Tentativa de ganhar memoria
del train_data
del valid_data


# In[4]:


# Visualiza as amostras
#num_samples = 20 # Numero de amostras que serao sorteadas para visualizacao
#resize = 3.5
#view_samples(train_dataset, train_labels, num_samples=num_samples, resize=resize,
#             title="Amostras de treinamento", color='gray')


# ---
# Treinamento
# ---------
# 
# Aprende com o dado usando a rede LeNet5.
# 
# ---

# In[5]:


# Prepara os datasets de treino e validacao para a rede
train_dataset = prepare_data_for_network(train_dataset, image_size)
train_labels = np.reshape(train_labels, (train_labels.shape[0], 1, 1, train_labels.shape[1]))

valid_dataset = prepare_data_for_network(valid_dataset, image_size)
valid_labels = np.reshape(valid_labels, (valid_labels.shape[0], 1, 1, valid_labels.shape[1]))


# In[8]:


# Definição de arquivos de saida - modelo treinado
model_file = "FCN_"+ str(iteration) + "_" + dataset_name + "_"
model_folder = "/opt/ml/model/" 
model_file = model_folder + model_file + str(image_size) + "x" + str(image_size) + ".ckpt"
weigths_file = model_folder + "FCN_" + dataset_name + "_" + str(iteration) + "_" + str(image_size) + "x" + str(image_size) + ".hdf5"

# Define hiper-parametros do treinamento
parser = argparse.ArgumentParser()
parser.add_argument("--batch-size",type=int)
parser.add_argument("--epochs",type=int)
parser.add_argument("--file-output",type=str)
parser.add_argument("--num-gpus",type=int)
args = parser.parse_args()
batch_size = args.batch_size
num_epochs = args.epochs
num_gpus = args.num_gpus
nome_do_arquivo = args.file_output
#batch_size = 589
starter_learning_rate = 0.1
decay_rate = 1e-2
decay_percentage = 0.50 # Porcentagem do numero de epocas para decair a taxa de aprendizagem 
dropout = 0.6
views_per_epoch = 1
target_size = (64,64)
train_size = train_dataset.shape[0]

# Imprime informacoes
print("Informacoes gerais:")
print(" - modelo:", model_file)
print(" - Conjunto de treinamento:")
print("    - Total:",train_size)
print(" - Conjunto de validacao:")
#print("    - Total:",validation_size)
print(" - Tamanho do batch:",batch_size)
print(" - Numero de epocas:",num_epochs)
print(" - Taxa de aprendizagem inicial:", starter_learning_rate)
print(" - Taxa de decaimento:", decay_rate)
print(" - GPUs solicitadas:", num_gpus)

#Registra o uso da GPU
#command = "nvidia-smi -q -l 15 -f " + nome_do_arquivo+".txt"
#args = shlex.split(command)
#subprocess.Popen(args)




# In[7]:


# Roda o treinamento
# Args da funcao run_training():
#       dataset: conjunto de dados de treinamento
#       labels: rotulos do treinamento
#       learning_rate: taxa de aprendizagem inicial
#       decay_rate: taxa de dacaimento da aprendizagem  
#       momentum: taxa de momento aplicada ao SGD 
#       num_steps: quantas epocas o treinamento ira realizar.
#       num_labels: quantidade de classes que possui no conjunto de treinamento
#       keep_prob: valor de 0.0 a 1.0 que regula o dropout da rede
#       batch_size: tamanho do batch. Se None, usa o dataset inteiro
#       train_size: tamanho do conjunto de treinamento (para fazer o split treino/valid)
#           Se None, assume que e para usar o batch inteiro para treinamento
#       target_size: tamanho de um dado de treinamento
#       validation_data: uma tupla contendo (conjunto de dados de validacao, labels)
#       save_file: arquivo para salvar o modelo treinado. Se None, nao salva nada
#       weights_file: arquivo para salvar os pesos do modelo treinado. Se None, nao salva nada
starter_time = time.time()
history = run_training(dataset=train_dataset,
                       labels=train_labels,
                       learning_rate=starter_learning_rate,
                       decay_rate=decay_rate,
                       momentum=0.9,
                       num_steps=num_epochs,
                       num_labels=2,
                       keep_prob=dropout,
                       batch_size=batch_size,
                       train_size=train_size,
                       target_size=target_size,
                       validation_data=(valid_dataset, valid_labels),
                       save_file=model_file,
                       weigths_file=weigths_file,
                       num_gpus=num_gpus)
duracao = time.time()-starter_time
print("Duracao do treinamento: ", duracao)

#command = "pkill nvidia-smi"
#args = shlex.split(command)
#subprocess.Popen(args)
# In[9]:


index = history.history['val_loss'].index(min(history.history['val_loss']))
with open('/opt/ml/output/accuracy.csv', 'a') as f:
    f.write(str(index))
    f.write(',')
    f.write(str(history.history['loss'][index]))
    f.write(',')
    f.write(str(history.history.get('acc',history.history.get('accuracy',0))[index]))
    f.write(',')
    f.write(str(history.history['val_loss'][index]))
    f.write(',')
    f.write(str(history.history.get('val_acc',history.history.get('val_accuracy',0))[index]))
    f.write(',')
    f.write(str(duracao))


# In[22]:


# Plota erro de treino e validacao ao longo das epocas

#plt.plot(history.history['loss']
#plt.plot(history.history['val_loss'])
#plt.title('Model loss')
#plt.ylabel('Loss')
#plt.xlabel('Epoch')
#plt.legend(['Train', 'Validation'], loc='upper right')
#plt.savefig(model_folder + 'graphics/loss_'+ str(iteration) + '.png')
#
#
## In[21]:
#
#
## Plota acuracia de treino e validacao ao longo das epocas
#plt.plot(history.history['acc'])
#plt.plot(history.history['val_acc'])
#plt.title('Model accuracy')
#plt.ylabel('Accuracy')
#plt.xlabel('Epoch')
#plt.legend(['Train', 'Validation'], loc='upper left')
#plt.savefig(model_folder + 'graphics/accuracy_'+ str(iteration) + '.png')

