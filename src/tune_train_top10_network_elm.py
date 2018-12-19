#-------------------------------------------------------------------------------
#
# TOP 10 with number of neurons on the hidden layer between 0 and 20;
#
#-------------------------------------------------------------------------------

#!/usr/bin/env python

from keras.models import Sequential
from keras.models import model_from_json
from keras.layers import Dense
from keras.layers.advanced_activations import LeakyReLU, PReLU, ReLU
from keras.utils import plot_model
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import numpy
from keras import metrics
from prettytable import PrettyTable
import time


# Prepare data
def prepare_data():
  # Load and prepare the dataset
  dataset = numpy.loadtxt("../data/tpcda19_02_dataset.csv", delimiter=",")

  # Synthesis of the information contained in variables u6 and u7
  dataset[:,5] = 0.4878*dataset[:,5] + 0.5261*dataset[:,6]

  # Remove variable u2 from the dataset
  dataset = dataset[:,[0,2,3,4,5,7]]

  # Split into input (X) and output (y) variables
  X = dataset[:,0:5]
  y = dataset[:,5]
  return X, y

# ELM - acho que tens que iniciar assim, nao?
def setWeights(model):
		weights = model.layers[-1].get_weights()
		weights[0] = numpy.random.random_sample((weights[0].shape[0],weights[0].shape[1]))
		model.layers[-1].set_weights(weights)

# Define the advanced model: 5 inputs -> [ N ] -> 1 output
def build_network(hidden_nodes, u1, u2):
  # Create model
  model = Sequential()

  #Input Variables: Input Layer, Hidden Layer            FALTA: trainable=False ?
  if u1=='leaky_relu':
    model.add(Dense(hidden_nodes, input_dim=5, use_bias=False, trainable=False ))
    setWeights(model) # FALTA ISTO NAO?
    # add an advanced activation
    model.add(LeakyReLU(alpha=0.01)) #BEST: 0.01
  else:
    model.add(Dense(hidden_nodes, input_dim=5,
                    activation=u1, use_bias=False, trainable=False ))
    setWeights(model) # FALTA ISTO NAO?

  # Output layer: Output Variable
  if u2=='leaky_relu':
    model.add(Dense(1, use_bias=False ))
    # add an advanced activation
    model.add(LeakyReLU(alpha=0.00)) # BEST: 0.00
  else:
    model.add(Dense(1,
                    activation=u2, use_bias=False ))

  # Configures the model for a mean squared error regression problem
  model.compile(loss='mean_squared_error', optimizer='rmsprop')
  # sgd, adam, rmsprop, adadelta
  return model

# Network training
def train_network(model, X_train, y_train, iter):
  # Trains the model for a given number of epochs (iterations on a dataset)
  history = model.fit(X_train, y_train, validation_split=0.10,
                      epochs=iter, batch_size=32, verbose=0) #shuffle=False,
  return history

# Evaluate Network Mean Squared Error
def evaluate_network(model, X_test, y_test):
  # Evaluate the model: Mean Squared Error (MSE)
  score = model.evaluate(X_test, y_test, batch_size=32)
  print ('MSE: ' + str(score))
  return score

# Find Top 10 Score
def find_top10score(score):
  _score = score[:]
  top10 = []
  _index = []
  # Find Top 10 Score
  for k in range(10):
    top10.append(min(_score))
    _index.append(_score.index(min(_score)))
    _score.remove(min(_score))
  return top10, _index

# Save TOP 10 models
def save_top10_models(model, _index):
  for k in range(10):
    # serialize model to JSON
    model_json = model[_index[k]].to_json()
    with open('../models/elm/elm_model_TOP'+str(k+1)+'.json', "w") as json_file:
      json_file.write(model_json)
    # serialize weights to HDF5
    model[_index[k]].save_weights('../models/elm/elm_model_TOP'+str(k+1)+'.h5')
  print("Saved models to disk")

# Find neural network config for Top 10
def find_top10config(score, top10, hidd_nodes, u_hidd, u_out):
  table = PrettyTable(['TOP','Nodes','u1','u2','MSE'])
  k=0
  for k in range(10):
    i=0
    #in All measureed scores
    for u1 in u_hidd:
      for u2 in u_out:
        for nodes in hidd_nodes:
          if score[i]==top10[k] and k < 10:
            table.add_row([k+1, nodes, u1, u2, top10[k]])
          i=i+1
  return table

# Save TOP10 on a .txt file
def save_top10(table):
  print ("\nSaving TOP 10 table...")
  data = table.get_string()
  with open('../data/elm_TOP10_TABLE.txt', 'wb') as f:
    f.write(data)
  print (table)

# Save TOP10 plots on a .png file
def save_top10plot(history, _index):
  print ("\nSaving TOP 10 MSE plots...")
  for k in range(10):
    # Plot training & validation loss values
    plt.plot(history[_index[k]].history['loss'])
    # Validation set
    plt.plot(history[_index[k]].history['val_loss'])
    plt.title('Model loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Test'], loc='upper right')
    # ax = plt.gca()
    # # Set x logaritmic
    # ax.set_yscale('log')
    #plt.show()
    plt.savefig('../imgs/elm/elm_TOP'+str(k+1)+'_ab.png')


# --------------------------------- MAIN ---------------------------------------
def main():

  # Load and prepare data
  X, y = prepare_data()

  # Split into Train dataset and Test data
  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.10)

  # Fix random seed for reproducibility
  numpy.random.seed(100)

  # --------------------------- Paramenters ------------------------------------
  # Define the way to set the initial random weights and bias
  #
  # zeros - initializer that generates tensors initialized to 0
  # ones - initializer that generates tensors initialized to 1
  # constant - "..." initialized to a constant value: (value=0)
  # random_normal - "..." normal distribution: (mean=0.0, stddev=0.05, seed=None)
  # random_uniform - "..." uniform distribution: (minval=-0.05, maxval=0.05, seed=None)
  # truncated_normal - "..." truncated normal distribution "...": (mean=0.0, stddev=0.05, seed=None)
  # VarianceScaling - "..." capable of adapting its scale to the shape of weights
  # orthogonal - "..." a random orthogonal matrix: (gain=1.0, seed=None)
  # Identity - "..." generates the identity matrix (Only use for 2D matrices): (gain=1.0)
  # lecun_uniform - LeCun uniform initializer: (seed=None)
  # glorot_normal - Glorot normal initializer, also called Xavier normal initializer: (seed=None)
  # glorot_uniform - Glorot uniform initializer, also called Xavier uniform initializer: (seed=None)
  # he_normal - He normal initializer: (seed=None)
  # lecun_normal: LeCun normal initializer: (seed=None)
  # he_uniform: He uniform variance scaling initializer: (seed=None)

  # Activation Functions
  #
  # softmax - softmax activation function: exp(z)/sum(exp(z))
  # softplus - softplus activation function: log(exp(x) + 1)
  # softsign - softsign activation function: x / (abs(x) + 1)
  # tanh - hyperbolic tangent activation function: tanh(x)
  # sigmoid - sigmoid activation function: 1 / (1 + exp(-x))
  # hard_sigmoid - hard sigmoid activation function: max(0, min(1, (x + 1)/2))
  # exponential - exponential (base e) activation function: exp(x)
  # elu - exponential linear unit: alfa*(exp(x) - 1),  x <= 0 | x, x > 0
  # selu - scaled Exponential Linear Unit (SELU): Y*alfa*(exp(x) - 1), Y*x < 0 | x, x >= 0
  # relu - rectified Linear Unit:  0,  x < 0 | x, x >= 0
  # linear - linear (i.e. identity) activation function: f(x) = x
  #
  # more complete resume:
  # - https://goo.gl/7hWj5y
  # sources:
  # - https://keras.io/activations/
  # - https://en.wikipedia.org/wiki/Activation_function
  #

  # TESTING: 2u1 x 2xu2 x 5nodes = 20 Networks
  # Hidden node activation function
  u_hidd = ['relu','leaky_relu'] # 'tanh'
  # Output node activation function
  u_out = ['relu','leaky_relu'] # better: leaky_relu > relu > linear > selu > elu

  # Create a Sequential model: [6 input] -> [12 neurons] -> [1 output]
  hidd_nodes = range(15,21) #0-20
  #nodes = 20
  epochs = 1000 # 1000 epochs Matlab default != iterations
  model = []
  train_history = []
  net_score = []
  time_elapsed_train = []
  time_elapsed_test = []
  i=1
  # Analyses MSE for 6^(possible) config's of networks
  for u1 in u_hidd:
    for u2 in u_out:
      for nodes in hidd_nodes:

        model.append(build_network(nodes, u1, u2))
        #train_history.append(train_network(model, X_train, y_train))
        time_start_train = time.clock()
        train_network(model[i-1], X_train, y_train, epochs)
        time_elapsed_train.append(time.clock() - time_start_train)
        time_start_test = time.clock()
        net_score.append(evaluate_network(model[i-1], X_test, y_test))
        time_elapsed_test.append(time.clock() - time_start_test)

        # Debug
        print("Model: ", nodes, u1, u2)
        print("Progress: %.2f%%" % (i/float(len(u_hidd)*len(u_out)
                                            *len(hidd_nodes))*100))
        #print(model.summary())
        #print(model.layers())
        i=i+1


  top10, _index = find_top10score(net_score)
  save_top10_models(model, _index)
  table = find_top10config(net_score, top10, hidd_nodes, u_hidd, u_out)
  save_top10(table)
  #save_top10plot(history, _index)
  print 'Mean Time Train: ', numpy.mean(time_elapsed_train)
  print 'Mean Time Test: ', numpy.mean(time_elapsed_test)


if __name__== "__main__":
  main()
