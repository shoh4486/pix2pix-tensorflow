# -*- coding: utf-8 -*-
"""
@author: sio277(shoh4486@naver.com)
tf.__version__ == '1.12.0' ~ '1.14.0'
"""
import tensorflow as tf
import numpy as np
from ops import *
from utils import *

def channel_generator():
    """
    The initial number of channels is input when class instantiation.
    """
    yield 64
    yield 128
    yield 256
    while 1:
        yield 512
        
class Pix2pix:
    """
    pix2pix by Isola, P. et al., Image-to-image translation with conditional adversarial networks, arXiv:1611.07004.
    """
    def __init__(self, sess, H_in, W_in, C_in, C_out, v_min, v_max, seed, loss_lambda=100.0, LSGAN=False, 
                 weight_decay_lambda=1e-07, truncated=False, optimizer='Adam', save_dir="./", gpu_num=2):
        """
        Parameters
        sess: TensorFlow session
        H_in, W_in, C_in: input shape (height, width, channel)
        C_out: output channel number (H_out==H_in, W_out==W_in)
        v_min, v_max: min and max of training data (for data de-normalization: from -1~1 to v_min~v_max)
        seed: random seed for random modules in numpy and TensorFlow
        loss_lambda: L1 loss lambda (pix2pix: 100.0)
        LSGAN: applying LSGAN loss
        weight_decay_lambda: L2 weight decay lambda (0.0: do not employ)
        truncated: truncated weight distribution
        optimizer: only Adam adopted
        save_dir: saving directory for the training results
        gpu_num: the number of gpus
        """
        self.sess = sess
        self.H = H_in
        self.W = W_in
        self.C_in = C_in
        self.C_out = C_out
        self.v_min = v_min
        self.v_max = v_max
        self._alpha = 0.5*(self.v_max - self.v_min)
        self._beta = 0.5*(self.v_max + self.v_min)
        self.seed = seed
        self.loss_lambda = loss_lambda
        self.LSGAN = LSGAN
        self.weight_decay_lambda = weight_decay_lambda
        self.truncated = truncated
        self.optimizer = optimizer
        self._beta1 = 0.5 # beta1 in Adam optimizer
        self.save_dir = save_dir
        self.gpu_num = gpu_num
        assert self.gpu_num < 3
        assert type(self.H) == int and type(self.W) == int, 'H and W should be integers.'
        self._H_list, self._W_list, self._C_list, self._s_list = [self.H], [self.W], [self.C_in], [] # _s_list: stride list
        C_ref = channel_generator()
        
        while 1: 
            if self._H_list[-1] == 3 or self._W_list[-1] == 3:
                self._H_list.append(int(np.ceil(self._H_list[-1]/3)))
                self._W_list.append(int(np.ceil(self._W_list[-1]/3)))
                self._C_list.append(next(C_ref))
                self._s_list.append(3) # if the number of H or W becomes 3 when reducing spatial dimensions, apply stride 3.
                break
                
            self._H_list.append(int(np.ceil(self._H_list[-1]/2)))
            self._W_list.append(int(np.ceil(self._W_list[-1]/2)))
            self._C_list.append(next(C_ref))
            self._s_list.append(2)
            if self._H_list[-1] == 1 or self._W_list[-1] == 1: break
  
        np.random.seed(self.seed)
        tf.set_random_seed(self.seed)
        self.build_model()

    def generator(self, c, batch_size, is_training, with_h=False):
        """
        Encoder-Decoder generator
        
        Parameters
        c: condition ([N, H, W, C_in])
        """
        h = []
        # ENCODER
        for i in range(len(self._H_list)-1):
            if i == 0: # first layer, no BN
                h.append(conv2d(c, self._C_list[i+1], 'g_h%d' % len(h), sdy=self._s_list[i], sdx=self._s_list[i], 
                                weight_decay_lambda=self.weight_decay_lambda, truncated=self.truncated))
            else:
                h.append(BN(conv2d(l_relu(h[-1]), self._C_list[i+1], 'g_h%d' % len(h), sdy=self._s_list[i], sdx=self._s_list[i],
                                   weight_decay_lambda=self.weight_decay_lambda, truncated=self.truncated), 
                            is_training, 'g_bn%d' % len(h)))
        
        # DECODER
        for j in range(len(self._H_list)-1):
            if j == 0:
                h.append(BN(t_conv2d(l_relu(h[-1]), [batch_size, self._H_list[-2-j], self._W_list[-2-j], self._C_list[-2-j]], 
                                     'g_h%d' % len(h), sdy=self._s_list[-1-j], sdx=self._s_list[-1-j], 
                                     weight_decay_lambda=self.weight_decay_lambda, truncated=self.truncated), 
                            is_training, 'g_bn%d' % len(h)))
            
            elif j > 0 and j < len(self._H_list)-2:
                h.append(BN(t_conv2d(tf.nn.relu(tf.concat([h[-1], h[-1-2*j]], axis=-1)), 
                                     [batch_size, self._H_list[-2-j], self._W_list[-2-j], self._C_list[-2-j]], 'g_h%d' % len(h), 
                                     sdy=self._s_list[-1-j], sdx=self._s_list[-1-j], 
                                     weight_decay_lambda=self.weight_decay_lambda, truncated=self.truncated), 
                            is_training, 'g_bn%d' % len(h)))
            
            else: # last layer, no BN, C=C_out
                h.append(t_conv2d(tf.nn.relu(tf.concat([h[-1], h[-1-2*j]], axis=-1)), 
                                  [batch_size, self._H_list[-2-j], self._W_list[-2-j], self.C_out], 'g_h%d' % len(h), 
                                  sdy=self._s_list[-1-j], sdx=self._s_list[-1-j], 
                                  weight_decay_lambda=self.weight_decay_lambda, truncated=self.truncated))
        
        h.append(tf.tanh(h[-1]))
        return h[-1] if not with_h else h

    def discriminator(self, image, c, is_training, with_h=False):
        """
        Encoder discriminator (patchGAN discriminator: C64-C128-C256-C512-C1)
        
        Parameters
        image: generation result OR ground truth ([N, H, W, C_out])
        c: condition ([N, H, W, C_in])
        """
        h = []
        h.append(conv2d(tf.concat([image, c], axis=-1), 64, 'd_h%d' % len(h), sdy=2, sdx=2, 
                        weight_decay_lambda=self.weight_decay_lambda, truncated=self.truncated))
        
        h.append(BN(conv2d(l_relu(h[-1]), 128, 'd_h%d' % len(h), sdy=2, sdx=2, 
                           weight_decay_lambda=self.weight_decay_lambda, truncated=self.truncated), 
                    is_training, 'd_bn%d' % len(h)))
        
        h.append(BN(conv2d(l_relu(h[-1]), 256, 'd_h%d' % len(h), sdy=2, sdx=2, 
                           weight_decay_lambda=self.weight_decay_lambda, truncated=self.truncated), 
                    is_training, 'd_bn%d' % len(h)))

        h.append(BN(conv2d(tf.pad(l_relu(h[-1]), [[0, 0], [1, 1], [1, 1], [0, 0]], mode='CONSTANT'), 512, 'd_h%d' % len(h), 
                           padding='VALID',
                           weight_decay_lambda=self.weight_decay_lambda, truncated=self.truncated), 
                    is_training, 'd_bn%d' % len(h)))
        
        h.append(conv2d(tf.pad(l_relu(h[-1]), [[0, 0], [1, 1], [1, 1], [0, 0]], mode='CONSTANT'), 1, 'd_h%d' % len(h), 
                        padding='VALID',
                        weight_decay_lambda=self.weight_decay_lambda, truncated=self.truncated)) # no BN

        h.append(tf.nn.sigmoid(h[-1]))
        return h[-2], h[-1] if not with_h else h
        
    def build_model(self):
        with tf.name_scope('placeholders'):
            with tf.name_scope('condition'):
                self.c = tf.placeholder(tf.float32, shape=(None, self.H, self.W, self.C_in), name='condition')
                
            with tf.name_scope('batch_size'):
                self.batch_size = tf.placeholder(tf.int32, shape=None, name='batch_size')
                
            with tf.name_scope('ground_truth'):
                self.x = tf.placeholder(tf.float32, shape=(None, self.H, self.W, self.C_out), name='ground_truth')
                
            with tf.name_scope('is_training'):
                self.is_training = tf.placeholder(tf.bool, shape=None, name='is_training')
                
            with tf.name_scope('learning_rate'):
                self.lr = tf.placeholder(tf.float32, shape=None, name='learning_rate')
                
        with tf.variable_scope('generator') as g_scope:
            if self.gpu_num == 2:
                with tf.device('/device:GPU:1'):
                    self.G_c = self.generator(self.c, self.batch_size, self.is_training, with_h=False)
                    g_scope.reuse_variables()
                    self.G_c_with_h = self.generator(self.c, self.batch_size, self.is_training, with_h=True)
            else:
                self.G_c = self.generator(self.c, self.batch_size, self.is_training, with_h=False)
                g_scope.reuse_variables()
                self.G_c_with_h = self.generator(self.c, self.batch_size, self.is_training, with_h=True)
                
        with tf.variable_scope('discriminator') as d_scope:
            self.D_x_logits, self.D_x = self.discriminator(self.x, self.c, self.is_training, with_h=False)
            d_scope.reuse_variables()
            self.D_G_c_logits, self.D_G_c = self.discriminator(self.G_c, self.c, self.is_training, with_h=False)
                
        with tf.name_scope('loss'):
            if self.LSGAN:
                D_loss_real = tf.reduce_mean(0.5*tf.square(self.D_x_logits - tf.ones_like(self.D_x_logits)))
                D_loss_fake = tf.reduce_mean(0.5*tf.square(self.D_G_c_logits - tf.zeros_like(self.D_G_c_logits))) 
                D_loss = tf.math.add(D_loss_real, D_loss_fake, name='D_loss')

                L1_loss = tf.reduce_mean(tf.abs(self.G_c - self.x))
                G_loss = tf.math.add(tf.reduce_mean(0.5*tf.square(self.D_G_c_logits - tf.ones_like(self.D_G_c_logits))), 
                                     self.loss_lambda*L1_loss, name='G_loss')
                
                if self.weight_decay_lambda:
                    weight_decay_vars = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)
                    D_weight_decay_list = [var for var in weight_decay_vars if 'd_' in var.name]
                    G_weight_decay_list = [var for var in weight_decay_vars if 'g_' in var.name]
                    D_loss += tf.add_n(D_weight_decay_list)
                    G_loss += tf.add_n(G_weight_decay_list)
                    
            else:
                D_loss_real = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=self.D_x_logits, 
                                                                                     labels=tf.ones_like(self.D_x_logits)))
                D_loss_fake = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=self.D_G_c_logits, 
                                                                                     labels=tf.zeros_like(self.D_G_c_logits)))
                D_loss = tf.math.add(D_loss_real, D_loss_fake, name='D_loss')

                L1_loss = tf.reduce_mean(tf.abs(self.G_c - self.x))
                G_loss = tf.math.add(tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=self.D_G_c_logits, 
                                                                                            labels=tf.ones_like(self.D_G_c_logits))),
                                     self.loss_lambda*L1_loss, name='G_loss')
                
                if self.weight_decay_lambda:
                    weight_decay_vars = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)
                    D_weight_decay_list = [var for var in weight_decay_vars if 'd_' in var.name]
                    G_weight_decay_list = [var for var in weight_decay_vars if 'g_' in var.name]
                    D_loss += tf.add_n(D_weight_decay_list)
                    G_loss += tf.add_n(G_weight_decay_list)

        with tf.name_scope('optimizer'):
            if self.optimizer == 'Adam':
                update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
                trainable_vars = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES)
                D_var_list = [var for var in trainable_vars if 'd_' in var.name]
                G_var_list = [var for var in trainable_vars if 'g_' in var.name]

                with tf.control_dependencies(update_ops):
                    self.D_train_step = tf.train.AdamOptimizer(learning_rate=self.lr, beta1=self._beta1).minimize(0.5*D_loss, var_list=D_var_list)
                    self.G_train_step = tf.train.AdamOptimizer(learning_rate=self.lr, beta1=self._beta1).minimize(G_loss, var_list=G_var_list)
            else:
                raise NotImplementedError('Other optimizers have not been considered.')
                
        with tf.name_scope('performance_measures'):
            with tf.name_scope('error'):
                self.MAE = tf.reduce_mean(tf.abs(self._alpha*(self.G_c - self.x)), name='MAE') # Mean Absolute Error
                self.MSE = tf.reduce_mean(tf.square(self._alpha*(self.G_c - self.x)), name='MSE') # Mean Squared Error
                
            with tf.name_scope('accuracy'):
                SSE = tf.reduce_sum(tf.square(self.G_c - self.x), axis=[1, 2, 3], name='SSE') # Sum of Squared Errors, [N, 1]
                SST = tf.reduce_sum(tf.square(self.x - tf.reshape(tf.reduce_mean(self.x, axis=[1, 2, 3]), [-1, 1, 1, 1])), 
                                    axis=[1, 2, 3], name='SST') # Total Sum of Squares, [N, 1]
                self.R2 = tf.reduce_mean(1.0 - SSE/SST, name='R2')
                self.PSNR = tf.reduce_mean(tf.image.psnr(0.5*self.G_c + 0.5, 0.5*self.x + 0.5, max_val=1.0), name='PSNR') 
                # returns [batch_size, 1] -> avg / -1~1 to 0~1
                self.SSIM = tf.reduce_mean(tf.image.ssim(0.5*self.G_c + 0.5, 0.5*self.x + 0.5, max_val=1.0), name='SSIM') 
                # returns [batch_size, 1] -> avg / -1~1 to 0~1
    
        gamma_var = [var for var in tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES) if 'gamma' in var.name]
        for gv in range(len(gamma_var)):
            tf.summary.histogram('gamma_var_%d' % gv, gamma_var[gv])
                
        beta_var = [var for var in tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES) if 'beta' in var.name]
        for bv in range(len(beta_var)):
            tf.summary.histogram('beta_var_%d' % bv, beta_var[bv])
        
        moving_var = [var for var in tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES) if 'moving_' in var.name] 
        # To consider this, batch_size should be larger than 1 due to BN cancellation in a bottleneck.
        for mv in range(len(moving_var)):
            tf.summary.histogram('moving_var_%d' % mv, moving_var[mv])
            
        weight_var = [var for var in tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES) if 'weight' in var.name]
        for wv in range(len(weight_var)):
            tf.summary.histogram('weight_var_%d' % wv, weight_var[wv])
        
        bias_var = [var for var in tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES) if 'bias' in var.name]
        for biv in range(len(bias_var)):
            tf.summary.histogram('bias_var_%d' % biv, bias_var[biv])
            
    def train(self, inputs, gts, config):    
        """
        Parameters
        inputs: a tuple consisting of (inputs_train, inputs_train_, inputs_valid) ([N, H, W, C_in]) (-1~1)
        gts: a tuple consisting of (gts_train, gts_train_, gts_valid) ([N, H, W, C_out]) (-1~1)
        config: configuration defined by tf.app.flags
        
        xxx_train: training data
        xxx_train_: to measure the training loss, acc
        xxx_valid: to measure the validation loss, acc
        """
        inputs_train, inputs_train_, inputs_valid = inputs
        gts_train, gts_train_, gts_valid = gts
        
        if config.start_epoch == 0:
            self.sess.run(tf.global_variables_initializer())
            
        merge = tf.summary.merge_all()
        writer = tf.summary.FileWriter(self.save_dir, self.sess.graph)
        
        self.MAE_train_vals, self.MSE_train_vals, self.R2_train_vals, self.PSNR_train_vals, self.SSIM_train_vals = [], [], [], [], []
        self.MAE_valid_vals, self.MSE_valid_vals, self.R2_valid_vals, self.PSNR_valid_vals, self.SSIM_valid_vals = [], [], [], [], []
        
        if not config.lr_decay:
            lr_tmp = config.lr_init
        else:
            raise NotImplementedError('lr_decay method was not adopted in pix2pix.')
    
        total_train_num = int(inputs_train.shape[0])
        iters_per_epoch = int(total_train_num/config.batch_size_training)
        
        for epoch in range(config.start_epoch, config.end_epoch):
            batch_number = np.random.RandomState(seed=epoch).choice(total_train_num, (iters_per_epoch, config.batch_size_training), replace=False)
            ############### 1 epoch ###############
            for i, batch in enumerate(batch_number):
                c_batch = inputs_train[batch].reshape(config.batch_size_training, self.H, self.W, self.C_in)
                x_batch = gts_train[batch].reshape(config.batch_size_training, self.H, self.W, self.C_out)        
                
                # update D
                self.sess.run(self.D_train_step, feed_dict={self.c: c_batch, self.batch_size: config.batch_size_training, 
                                                            self.x: x_batch, self.is_training: True, self.lr: lr_tmp})
                # update G
                self.sess.run(self.G_train_step, feed_dict={self.c: c_batch, self.batch_size: config.batch_size_training, 
                                                            self.x: x_batch, self.is_training: True, self.lr: lr_tmp})
            #######################################
            
            if epoch % config.check_epoch == 0:
                self.G_c_train, MAE_train_val, MSE_train_val, R2_train_val, PSNR_train_val, SSIM_train_val, summary_val = self.sess.run([self.G_c, self.MAE, self.MSE, self.R2, self.PSNR, self.SSIM, merge], 
                                                                                                                                        feed_dict={self.c: inputs_train_, self.batch_size: len(inputs_train_), 
                                                                                                                                                   self.x: gts_train_, self.is_training: True}) # is_training: True by pix2pix policy
                self.MAE_train_vals.append(MAE_train_val)
                self.MSE_train_vals.append(MSE_train_val)
                self.R2_train_vals.append(R2_train_val)
                self.PSNR_train_vals.append(PSNR_train_val)
                self.SSIM_train_vals.append(SSIM_train_val)
                writer.add_summary(summary_val, epoch) 
                
                self.G_c_valid, MAE_valid_val, MSE_valid_val, R2_valid_val, PSNR_valid_val, SSIM_valid_val = self.sess.run([self.G_c, self.MAE, self.MSE, self.R2, self.PSNR, self.SSIM], 
                                                                                                                           feed_dict={self.c: inputs_valid, self.batch_size: len(inputs_valid), 
                                                                                                                                      self.x: gts_valid, self.is_training: True})
                self.MAE_valid_vals.append(MAE_valid_val)
                self.MSE_valid_vals.append(MSE_valid_val)
                self.R2_valid_vals.append(R2_valid_val)
                self.PSNR_valid_vals.append(PSNR_valid_val)
                self.SSIM_valid_vals.append(SSIM_valid_val)
                
                print('Epoch: %d, RMSE_train: %f, RMSE_valid: %f, R2_train: %f, R2_valid: %f' % (epoch, self.MSE_train_vals[-1]**0.5, self.MSE_valid_vals[-1]**0.5, self.R2_train_vals[-1], self.R2_valid_vals[-1]))
                    
    def evaluation(self, inputs, gts=None, with_h=False):
        """
        inputs: conditions ([N, H, W, C_in]) (-1~1)       
        gts: ground truths ([N, H, W, C_out]) (-1~1)
        """
        if np.sum(gts == None):
            if not with_h:
                return self.sess.run(self.G_c, feed_dict={self.c: inputs, self.batch_size: len(inputs), self.is_training: True})
            else:
                return self.sess.run(self.G_c_with_h, feed_dict={self.c: inputs, self.batch_size: len(inputs), self.is_training: True})
            
        else: # gts is given
            if not with_h:
                return self.sess.run([self.G_c, self.MAE, self.MSE, self.R2, self.PSNR, self.SSIM], feed_dict={self.c: inputs, 
                                                                                                               self.batch_size: len(inputs),
                                                                                                               self.x: gts,
                                                                                                               self.is_training: True})
            else:
                return self.sess.run([self.G_c_with_h, self.MAE, self.MSE, self.R2, self.PSNR, self.SSIM], feed_dict={self.c: inputs, 
                                                                                                                      self.batch_size: len(inputs),
                                                                                                                      self.x: gts,
                                                                                                                      self.is_training: True})