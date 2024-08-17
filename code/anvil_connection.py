# -*- coding: utf-8 -*-
"""Anvil_Connection.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1zizB1yKvTc1Vpr97CIbpZtQf_OfhUCp5
"""

#!pip install anvil-uplink

import tensorflow as tf
from tensorflow.keras import models
import anvil.media

import anvil.server
import anvil.mpl_util 
import numpy as np
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt


class ClassToken(tf.keras.layers.Layer):
    def __init__(self):
        super().__init__()

    def build(self, input_shape):
        w_init = tf.random_normal_initializer()
        self.w = tf.Variable(
            initial_value = w_init(shape=(1, 1, input_shape[-1]), dtype=tf.float32),
            trainable = True
        )

    def call(self, inputs):
        batch_size = tf.shape(inputs)[0]
        hidden_dim = self.w.shape[-1]

        cls = tf.broadcast_to(self.w, [batch_size, 1, hidden_dim])
        cls = tf.cast(cls, dtype=inputs.dtype)
        return cls

model_cnn = models.load_model('model_cnn.h5')
model_transformer = models.load_model('model_tf.h5', custom_objects={'ClassToken': ClassToken})

n = 7  # Number of rows of blocks
m = 7  # Number of columns of blocks
block_size = 16  # Size of each block (e.g., 4x4 pixels per block)

@anvil.server.callable
def predict_models(uploaded_file):
    print("[Server] predict_models function started")
    if not uploaded_file.content_type == 'text/csv':
        return "The file is not a CSV."
    
    data = pd.read_csv(BytesIO(uploaded_file.get_bytes()), header=None)

    if data is None or data.shape != (28, 28):
        return "The CSV file is not in the correct format. It must be 28x28."

    # Scale data if necessary
    
    data_scaled = data.values / 255.0 if data.values.max() > 1 else data

    # Reshape data for the CNN model
    image_cnn = data_scaled.reshape(1, 28, 28, 1)  # Add batch dimension

    # Predict with the CNN model
    prediction_cnn = model_cnn.predict(image_cnn)
    predicted_digit_cnn = np.argmax(prediction_cnn, axis=1)
    print(f"[Local] CNN Prediction: {predicted_digit_cnn[0]}")


    #Transformer Model
    ndata_tf = 1  # Since you're working with one image at a time

    x_ravel_tf = np.zeros((ndata_tf,n*m,block_size))
    ind = 0
    for row in range(n):
        for col in range(m):
            # Extract a 4x4 block and flatten it
            block = data_scaled[(row*4):((row+1)*4), (col*4):((col+1)*4)].flatten()

            # If the block has fewer than 16 elements, pad with zeros
            if block.size < block_size:
                block = np.pad(block, (0, block_size - block.size), 'constant')

            x_ravel_tf[0, ind, :] = block  # Note the use of 0 instead of img
            ind += 1

    pos_feed_train = np.array([list(range(n * m))])

    # Predict with Transformer
    prediction_transformer = model_transformer.predict([x_ravel_tf, pos_feed_train])
    predicted_digit_transformer = np.argmax(prediction_transformer, axis=1)
    print(f"[Local] Transformer Prediction: {predicted_digit_transformer[0]}")


    return [predicted_digit_cnn[0], predicted_digit_transformer[0]]

    
@anvil.server.callable
def generate_image(uploaded_file):
    # Read the file content as bytes and then use BytesIO to treat it as a file-like object
    
    data = pd.read_csv(BytesIO(uploaded_file.get_bytes()), header=None)

    plt.figure(figsize=(3, 3))
    plt.imshow(data, cmap='gray')
    plt.axis('off')

    # Directly convert the matplotlib plot to an Anvil media object
    plot_media = anvil.mpl_util.plot_image()
    
    plt.clf()
    plt.close('all')
    
    return plot_media


anvil.server.connect("server_Z75IMOCSMK2DSHMO5VUSVS7B-ANUE7DMJU4HA6XTE")

print("[Server] Anvil Uplink connected successfully.")

anvil.server.wait_forever()