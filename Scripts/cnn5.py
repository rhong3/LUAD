#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convolutional neural nets driving code for TF2.0 and Xeption

Created on 04/26/2019

@author: RH
"""
from datetime import datetime
import os
import sys
import time
import numpy as np
import tensorflow as tf
import Accessory2 as ac


class INCEPTION():
    # hyper parameters
    DEFAULTS = {
        "batch_size": 128,
        "dropout": 0.5,
        "learning_rate": 1E-3,
        "classes": 4
    }

    RESTORE_KEY = "cnn_to_restore"

    def __init__(self, input_dim, d_hyperparams={},
                 save_graph_def=True, meta_graph=None,
                 log_dir="./log", meta_dir="./meta", model='IG'):

        self.input_dim = input_dim
        self.__dict__.update(INCEPTION.DEFAULTS, **d_hyperparams)
        self.sesh = tf.Session()
        self.model = model

        if meta_graph:  # load saved graph
            model_name = os.path.basename(meta_graph)
            meta_graph = os.path.abspath(meta_graph)
            tf.train.import_meta_graph(meta_dir + '/' + model_name +'.meta').restore(
                self.sesh, meta_dir + '/' + model_name)
            handles = self.sesh.graph.get_collection(INCEPTION.RESTORE_KEY)


        else:  # build graph from scratch
            self.datetime = datetime.now().strftime(r"%y%m%d_%H%M")
            handles = self._buildGraph(self.model)
            for handle in handles:
                tf.add_to_collection(INCEPTION.RESTORE_KEY, handle)
            self.sesh.run(tf.global_variables_initializer())

        # unpack handles for tensor ops to feed or fetch for lower layers
        (self.xa_in, self.xb_in, self.xc_in, self.is_train, self.y_in, self.logits,
         self.net, self.w, self.pred, self.pred_cost,
         self.global_step, self.train_op, self.merged_summary) = handles

        if save_graph_def:  # tensorboard
            try:
                os.mkdir(log_dir + '/training')
                os.mkdir(log_dir + '/validation')

            except FileExistsError:
                pass

            self.train_logger = tf.summary.FileWriter(log_dir + '/training', self.sesh.graph)
            self.valid_logger = tf.summary.FileWriter(log_dir + '/validation', self.sesh.graph)

    @property
    def step(self):
        return self.global_step.eval(session=self.sesh)

    # build graph; choose a structure defined in model
    def _buildGraph(self, model):
        # image input
        xa_in = tf.placeholder(tf.float32, name="x")
        xa_in_reshape = tf.reshape(xa_in, [-1, self.input_dim[1], self.input_dim[2], 3])
        xb_in = tf.placeholder(tf.float32, name="x")
        xb_in_reshape = tf.reshape(xb_in, [-1, self.input_dim[1], self.input_dim[2], 3])
        xc_in = tf.placeholder(tf.float32, name="x")
        xc_in_reshape = tf.reshape(xc_in, [-1, self.input_dim[1], self.input_dim[2], 3])
        # dropout
        dropout = self.dropout
        # dropout = tf.placeholder_with_default(1., shape=[], name="dropout")
        # label input
        y_in = tf.placeholder(dtype=tf.float32, name="y")
        # train or test
        is_train = tf.placeholder_with_default(True, shape=[], name="is_train")
        # classes = tf.placeholder_with_default(4, shape=[], name="num_classes")
        classes = self.classes

        if model == 'X1':
            import XeptionV1
            logits, nett, ww = XeptionV1.XecptionV1(xa_in_reshape, xb_in_reshape, xc_in_reshape,
                                                   num_cls=classes,
                                                   is_train=is_train,
                                                   dropout=dropout,
                                                   scope='XecptionV1')
            print('Using Xeption-V1')
        else:
            import XeptionV1
            logits, nett, ww = XeptionV1.XecptionV1(xa_in_reshape, xb_in_reshape, xc_in_reshape,
                                                   num_cls=classes,
                                                   is_train=is_train,
                                                   dropout=dropout,
                                                   scope='XecptionV1')
            print('Using Default: Xeption-V1')

        pred = tf.nn.softmax(logits, name="prediction")

        global_step = tf.Variable(0, trainable=False)

        pred_cost = tf.losses.softmax_cross_entropy(
            onehot_labels=y_in, logits=logits)

        tf.summary.scalar("{}_cost".format(model), pred_cost)

        tf.summary.tensor_summary("{}_pred".format(model), pred)

        # opt = tf.optimizers.Adam(learning_rate=self.learning_rate) ---------TF2.0
        opt = tf.train.AdamOptimizer(learning_rate=self.learning_rate)
        train_op = opt.minimize(loss=pred_cost, global_step=global_step)

        merged_summary = tf.summary.merge_all()

        return (xa_in, xb_in, xc_in, is_train,
                y_in, logits, nett, ww, pred, pred_cost,
                global_step, train_op, merged_summary)

    # inference using trained models
    def inference(self, X, dirr, testset=None, pmd=None, train_status=False, Not_Realtest=True, bs=None):
        now = datetime.now().isoformat()[11:]
        print("------- Testing begin: {} -------\n".format(now), flush=True)
        rd = 0
        pdx = []
        yl = []
        if Not_Realtest:
            itr, file, ph = X.data(train=False)
            next_element = itr.get_next()
            with tf.Session() as sessa:
                sessa.run(itr.initializer, feed_dict={ph: file})
                while True:
                    try:
                        xa, xb, xc, y = sessa.run(next_element)
                        feed_dict = {self.xa_in: xa, self.xb_in: xb, self.xc_in: xc, self.is_train: train_status}
                        fetches = [self.pred, self.net, self.w]
                        pred, net, w = self.sesh.run(fetches, feed_dict)
                        # ac.CAM(net, w, pred, xc, y, dirr, 'Test', bs, pmd, rd)
                        if rd == 0:
                            pdx = pred
                            yl = y
                        else:
                            pdx = np.concatenate((pdx, pred), axis=0)
                            yl = np.concatenate((yl, y), axis=0)
                        rd += 1
                    except tf.errors.OutOfRangeError:
                        ac.metrics(pdx, yl, dirr, 'Test', pmd, testset)
                        break
        else:
            itr, file, ph = X.data(Not_Realtest=False, train=False)
            next_element = itr.get_next()
            with tf.Session() as sessa:
                sessa.run(itr.initializer, feed_dict={ph: file})
                while True:
                    try:
                        xa, xb, xc = sessa.run(next_element)
                        feed_dict = {self.xa_in: xa, self.xb_in: xb, self.xc_in: xc, self.is_train: train_status}
                        fetches = [self.pred, self.net, self.w]
                        pred, net, w = self.sesh.run(fetches, feed_dict)
                        # ac.CAM_R(net, w, pred, xc, dirr, 'Test', bs, rd)
                        if rd == 0:
                            pdx = pred
                        else:
                            pdx = np.concatenate((pdx, pred), axis=0)
                        rd += 1
                    except tf.errors.OutOfRangeError:
                        ac.realout(pdx, dirr, 'Test', pmd)
                        break

        now = datetime.now().isoformat()[11:]
        print("------- Testing end: {} -------\n".format(now), flush=True)

    # get global step
    def get_global_step(self, X):
        itr, file, ph = X.data()
        next_element = itr.get_next()
        with tf.Session() as sessa:
            sessa.run(itr.initializer, feed_dict={ph: file})
            xa, xb, xc, y = sessa.run(next_element)
            feed_dict = {self.xa_in: xa, self.xb_in: xb, self.xc_in: xc, self.y_in: y}

            fetches = [self.global_step]

            i = self.sesh.run(fetches, feed_dict)

        return i

    # training
    def train(self, X, VAX, ct, bs, dirr, pmd, max_iter=np.inf, cross_validate=True, verbose=True, save=True, outdir="./out"):
        start_time = time.time()
        svs = 0
        if save:
            saver = tf.train.Saver(tf.global_variables(), max_to_keep=None)

        try:
            err_train = 0
            now = datetime.now().isoformat()[11:]
            print("------- Training begin: {} -------\n".format(now), flush=True)
            itr, file, ph = X.data()
            next_element = itr.get_next()

            vaitr, vafile, vaph = VAX.data(train=False)
            vanext_element = vaitr.get_next()

            with tf.Session() as sessa:
                sessa.run(itr.initializer, feed_dict={ph: file})
                sessa.run(vaitr.initializer, feed_dict={vaph: vafile})
                train_cost = []
                validation_cost = []
                valid_cost = 0
                while True:
                    try:
                        xa, xb, xc, y = sessa.run(next_element)

                        feed_dict = {self.xa_in: xa, self.xb_in: xb, self.xc_in: xc, self.y_in: y}

                        fetches = [self.merged_summary, self.logits, self.pred,
                                   self.pred_cost, self.global_step, self.train_op]

                        summary, logits, pred, cost, i, _ = self.sesh.run(fetches, feed_dict)

                        self.train_logger.add_summary(summary, i)
                        err_train += cost

                        if i < 2:
                            train_cost.append(cost)

                        try:
                            mintrain = min(train_cost)
                        except ValueError:
                            mintrain = 0

                        if cost <= mintrain and i > 29999:
                            if cross_validate:
                                temp_valid = []
                                for iii in range(10):
                                    xa, xb, xc, y = sessa.run(vanext_element)
                                    feed_dict = {self.xa_in: xa, self.xb_in: xb, self.xc_in: xc, self.y_in: y,
                                                 self.is_train: False}
                                    fetches = [self.pred_cost, self.merged_summary]
                                    valid_cost, valid_summary = self.sesh.run(fetches, feed_dict)
                                    self.valid_logger.add_summary(valid_summary, i)
                                    temp_valid.append(valid_cost)

                                tempminvalid = np.mean(temp_valid)
                                try:
                                    minvalid = min(validation_cost)
                                except ValueError:
                                    minvalid = 0

                                if tempminvalid <= minvalid:
                                    train_cost.append(cost)
                                    print("round {} --> loss: ".format(i), cost, flush=True)
                                    print("round {} --> validation loss: ".format(i), tempminvalid, flush=True)
                                    print("New Min loss model found!")
                                    validation_cost.append(tempminvalid)
                                    if save:
                                        outfile = os.path.join(os.path.abspath(outdir),
                                                               "{}_{}".format(self.model,
                                                                              "_".join(['dropout', str(self.dropout)])))
                                        saver.save(self.sesh, outfile, global_step=None)
                                        svs = i

                            else:
                                train_cost.append(cost)
                                print("round {} --> loss: ".format(i), cost, flush=True)
                                print("New Min loss model found!")
                                if save:
                                    outfile = os.path.join(os.path.abspath(outdir),
                                                           "{}_{}".format(self.model,
                                                                          "_".join(['dropout', str(self.dropout)])))
                                    saver.save(self.sesh, outfile, global_step=None)
                                    svs = i
                        else:
                            train_cost.append(cost)

                        if i % 1000 == 0 and verbose:
                            print("round {} --> loss: ".format(i), cost, flush=True)
                            if cross_validate:
                                temp_valid = []
                                for iii in range(100):
                                    xa, xb, xc, y = sessa.run(vanext_element)
                                    feed_dict = {self.xa_in: xa, self.xb_in: xb, self.xc_in: xc, self.y_in: y,
                                                 self.is_train: False}
                                    fetches = [self.pred_cost, self.merged_summary]
                                    valid_cost, valid_summary = self.sesh.run(fetches, feed_dict)
                                    self.valid_logger.add_summary(valid_summary, i)
                                    temp_valid.append(valid_cost)
                                tempminvalid = np.mean(temp_valid)
                                try:
                                    minvalid = min(validation_cost)
                                except ValueError:
                                    minvalid = 0
                                validation_cost.append(tempminvalid)
                                print("round {} --> Step Average validation loss: ".format(i), tempminvalid, flush=True)

                                if save and tempminvalid <= minvalid:
                                    print("New Min loss model found!")
                                    print("round {} --> loss: ".format(i), cost, flush=True)
                                    outfile = os.path.join(os.path.abspath(outdir),
                                                           "{}_{}".format(self.model,
                                                                          "_".join(['dropout', str(self.dropout)])))
                                    saver.save(self.sesh, outfile, global_step=None)
                                    svs = i

                                if i > 79999:
                                    valid_mean_cost = np.mean(validation_cost[-10:-1])
                                    print('Mean validation loss: {}'.format(valid_mean_cost))
                                    if valid_cost > valid_mean_cost:
                                        print("Early stopped! No improvement for at least 10000 iterations")
                                        break
                                    else:
                                        print("Passed early stopping evaluation. Continue training!")

                        if i >= max_iter-2 and verbose:
                            if cross_validate:
                                print("final avg loss (@ step {} = epoch {}): {}".format(
                                    i + 1, np.around(i / ct * bs), err_train / i), flush=True)

                                now = datetime.now().isoformat()[11:]
                                print("------- Training end: {} -------\n".format(now), flush=True)

                                now = datetime.now().isoformat()[11:]
                                print("------- Final Validation begin: {} -------\n".format(now), flush=True)
                                xa, xb, xc, y = sessa.run(vanext_element)
                                feed_dict = {self.xa_in: xa, self.xb_in: xb, self.xc_in: xc, self.y_in: y,
                                             self.is_train: False}
                                fetches = [self.pred_cost, self.merged_summary]
                                valid_cost, valid_summary= self.sesh.run(fetches, feed_dict)

                                self.valid_logger.add_summary(valid_summary, i)
                                print("round {} --> Final Last validation loss: ".format(i), valid_cost, flush=True)
                                now = datetime.now().isoformat()[11:]
                                print("------- Final Validation end: {} -------\n".format(now), flush=True)
                            try:
                                self.train_logger.flush()
                                self.train_logger.close()
                                self.valid_logger.flush()
                                self.valid_logger.close()

                            except(AttributeError):  # not logging
                                print('Not logging', flush=True)
                            break

                    except tf.errors.OutOfRangeError:
                        if cross_validate:
                            print("final avg loss (@ step {} = epoch {}): {}".format(
                                i + 1, np.around(i / ct * bs), err_train / i), flush=True)

                            now = datetime.now().isoformat()[11:]
                            print("------- Training end: {} -------\n".format(now), flush=True)

                            now = datetime.now().isoformat()[11:]
                            print("------- Final Validation begin: {} -------\n".format(now), flush=True)
                            xa, xb, xc, y = sessa.run(vanext_element)
                            feed_dict = {self.xa_in: xa, self.xb_in: xb, self.xc_in: xc, self.y_in: y,
                                         self.is_train: False}
                            fetches = [self.pred_cost, self.merged_summary, self.pred, self.net, self.w]
                            valid_cost, valid_summary, pred, net, w = self.sesh.run(fetches, feed_dict)

                            self.valid_logger.add_summary(valid_summary, i)
                            print("round {} --> Final Last validation loss: ".format(i), valid_cost, flush=True)
                            ac.CAM(net, w, pred, xc, y, dirr, 'Validation', bs, pmd)
                            ac.metrics(pred, y, dirr, 'Validation', pmd)
                            now = datetime.now().isoformat()[11:]
                            print("------- Final Validation end: {} -------\n".format(now), flush=True)

                        try:
                            self.train_logger.flush()
                            self.train_logger.close()
                            self.valid_logger.flush()
                            self.valid_logger.close()

                        except(AttributeError):  # not logging
                            print('Not logging', flush=True)

                        break
                try:
                    print("final avg loss (@ step {} = epoch {}): {}".format(
                        i + 1, np.around(i / ct * bs), err_train / i), flush=True)

                    now = datetime.now().isoformat()[11:]
                    print("------- Training end: {} -------\n".format(now), flush=True)

                    if svs < 15000 and save:
                            print("Save the last model as the best model.")
                            outfile = os.path.join(os.path.abspath(outdir),
                                                   "{}_{}".format(self.model, "_".join(['dropout', str(self.dropout)])))
                            saver.save(self.sesh, outfile, global_step=None)

                    if cross_validate:
                        now = datetime.now().isoformat()[11:]
                        print("------- Validation begin: {} -------\n".format(now), flush=True)
                        xa, xb, xc, y = sessa.run(vanext_element)
                        feed_dict = {self.xa_in: xa, self.xb_in: xb, self.xc_in: xc, self.y_in: y, self.is_train: False}
                        fetches = [self.pred_cost, self.merged_summary, self.pred, self.net, self.w]
                        valid_cost, valid_summary, pred, net, w = self.sesh.run(fetches, feed_dict)

                        self.valid_logger.add_summary(valid_summary, i)
                        print("round {} --> Last validation loss: ".format(i), valid_cost, flush=True)
                        ac.CAM(net, w, pred, xc, y, dirr, 'Validation', bs, pmd)
                        ac.metrics(pred, y, dirr, 'Validation', pmd)
                        now = datetime.now().isoformat()[11:]
                        print("------- Validation end: {} -------\n".format(now), flush=True)

                    try:
                        self.train_logger.flush()
                        self.train_logger.close()
                        self.valid_logger.flush()
                        self.valid_logger.close()

                    except(AttributeError):  # not logging
                        print('Not logging', flush=True)

                except tf.errors.OutOfRangeError:
                    print("final avg loss (@ step {} = epoch {}): {}".format(
                        i + 1, np.around(i / ct * bs), err_train / i), flush=True)

                    now = datetime.now().isoformat()[11:]
                    print("------- Training end: {} -------\n".format(now), flush=True)
                    print('No more validation needed!')

            print("--- %s seconds ---" % (time.time() - start_time))

        except(KeyboardInterrupt):

            print("final avg loss (@ step {} = epoch {}): {}".format(
                i, np.around(i / ct * bs), err_train / i), flush=True)

            now = datetime.now().isoformat()[11:]
            print("------- Training end: {} -------\n".format(now), flush=True)

            if save:
                outfile = os.path.join(os.path.abspath(outdir),
                                       "{}_{}".format(self.model, "_".join(['dropout', str(self.dropout)])))
                saver.save(self.sesh, outfile, global_step=None)
            try:
                self.train_logger.flush()
                self.train_logger.close()
                self.valid_logger.flush()
                self.valid_logger.close()

            except(AttributeError):  # not logging
                print('Not logging', flush=True)

            sys.exit(0)

