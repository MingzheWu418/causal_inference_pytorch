# import ast
import csv

import pandas as pd
import numpy as np
import json

import sklearn
from sklearn.preprocessing import StandardScaler, Normalizer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from scipy.special import expit


# Initial approach:
class format_processor:

    def __init__(self):
        """
        Create a data loader
        """

        # self.data typically contains the following information,
        # where t is the observed treatment,
        # yf the factual outcome, ycf the counter factual
        # and x is the other features
        self.data = {"t": [], "yf": [], "ycf": [], "x": []}
        self.dataset = ""
        self.filename = ""

    def load_data(self, dataset):
        """
        Load data of a particular dataset
        :param dataset: the name of the dataset, case insensitive
        :return: the dataset loaded
        """

        name = dataset.upper()
        assert name in ["TWINS", "IHDP", "JOBS"]
        self.dataset = name
        self.filename = "../datasets/" + name + "/"

        # Have to hard code each dataset, given each dataset has different structure
        if self.dataset == "TWINS":
            self.data = self.__load_TWINS()
        elif self.dataset == "IHDP":
            self.data = self.__load_IHDP()
            # print(self.data)
        elif self.dataset == "JOBS":
            pass
        else:
            pass
        return self.data

    def data_simulate(self, mode):
        pass

    def __load_TWINS(self):
        """
        Private helper to load TWINS.
        Notice controlled group (T == 0) is always saved in the first half of an array,
        and treatment group (T == 1) always saved in the last half of an array.

        :return: the data loaded
        """
        data = {}

        """Load twins data."""

        # Load original data (11400 patients, 30 features, 2 dimensional potential outcomes)
        ori_data = np.loadtxt("../datasets/TWINS/Twin_data.csv", delimiter=",",skiprows=1)
        # Define features
        x = ori_data[:,:30]
        no, dim = x.shape

        # Define potential outcomes
        potential_y = ori_data[:, 30:]
        # Die within 1 year = 1, otherwise = 0
        potential_y = np.array(potential_y < 9999,dtype=float)

        ## Assign treatment
        coef = np.random.uniform(-0.01, 0.01, size = [dim,1])
        prob_temp = expit(np.matmul(x, coef) + np.random.normal(0,0.01, size = [no,1]))

        prob_t = prob_temp/(2*np.mean(prob_temp))
        prob_t[prob_t>1] = 1

        t = np.random.binomial(1,prob_t,[no,1])
        t = t.reshape([no,])

        ## Define observable outcomes
        # y = np.zeros([no,1])
        y = np.transpose(t) * potential_y[:,1] + np.transpose(1-t) * potential_y[:,0]
        ycf = np.transpose(1-t) * potential_y[:,1] + np.transpose(t) * potential_y[:,0]
        y = np.reshape(np.transpose(y), [no, ])
        ycf = np.reshape(np.transpose(ycf), [no, ])
        data["t"] = t
        data["yf"] = y
        data["ycf"] = ycf
        data["x"] = x

        # for i in range(no):
        #     print(y[i], ycf[i])
        # # Read in treatment
        # t = pd.read_csv(self.filename + "twin_pairs_T_3years_samesex.csv")
        # # Store T as 2Nx1 np array, and T0, T1.
        # # Here T is saved as binary values,
        # # while T0 and T1 contains the weights of infants
        # data["t"] = np.append(np.zeros(len(t["dbirwt_0"])), np.ones(len(t["dbirwt_1"]))).reshape(-1,1)
        # # data["t0"] = t["dbirwt_0"].to_numpy().reshape(-1,1)
        # # data["t1"] = t["dbirwt_1"].to_numpy().reshape(-1,1)
        # # data["t"] = pd.concat([np.zeros(t["dbirwt_0"].shape), np.zeros(t["dbirwt_1"])], ignore_index=True).to_numpy().reshape(-1,1)
        #
        # # Read in outcome
        # y = pd.read_csv(self.filename + "twin_pairs_Y_3years_samesex.csv")
        # # Store y0, y1 as they are. yf is the concatenation of y0 and y1,
        # # data["y0"] = y["mort_0"].to_numpy().reshape(-1,1)
        # # data["y1"] = y["mort_1"].to_numpy().reshape(-1,1)
        # data["yf"] = pd.concat([y["mort_0"], y["mort_1"]], ignore_index=True).to_numpy().reshape(-1,1)
        # data["ycf"] = 1-data["yf"].reshape(-1,1)
        # # Read in other factors
        # x = pd.read_csv(self.filename + "twin_pairs_X_3years_samesex.csv")
        # x = x.iloc[:, 2:]
        #
        # # 2D array, first axis is variables, second axis is instances
        # # i.e. data["X"][0] returns the value of the first X variable for all patients
        # x0 = x.loc[:, ~x.columns.isin(["infant_id_1", "bord_1"])]
        # x1 = x.loc[:, ~x.columns.isin(["infant_id_0", "bord_0"])]
        # x0 = x0.rename(columns={"infant_id_0": "infant_id", "bord_0": "bord"})
        # x1 = x1.rename(columns={"infant_id_1": "infant_id", "bord_1": "bord"})
        # x_concat = pd.concat([x0, x1], ignore_index=True)
        # data["x"] = x_concat.to_numpy()

        # We also keep the label for each row
        # data["x_label"] = x_concat.columns.to_numpy()

        """
        # This part served as keeping track of the type of each variable:
        # whether it is binary, categorical, or numerical.
        
        file = open(self.filename + "covar_type.txt", "r")
        contents = file.read()
        dictionary = ast.literal_eval(contents)
        file.close()
        data["label_type"] = dictionary
        """

        # Have to manually input this part based on prior knowledge
        # data["raw"] = {"T": 1, "Y0": 1, "Y1": 1, "Y": 1, "X": 1}
        return data

    def __load_IHDP(self):
        """
        Private helper to load IHDP
        :return: the data loaded
        """
        # Initialization
        data = {}

        # Read in datasets
        dataset = pd.read_csv(self.filename + "csv/ihdp_npci_1.csv", header=None)
        for index in range(2, 11):
            dataset = pd.concat([dataset, pd.read_csv(self.filename + "csv/ihdp_npci_" + str(index) + ".csv", header=None)])
            dataset = dataset.reset_index().drop(columns=["index"])

        # Assign column names
        col = ["treatment", "y_factual", "y_cfactual", "mu0", "mu1", ]
        for i in range(1, 26):
            col.append("x" + str(i))
        dataset.columns = col

        # Directly store T, Y, and X from the dataset
        # Also store them as Nx1 numpy array
        data["t"] = dataset["treatment"].to_numpy().reshape(-1,1)
        data["yf"] = dataset["y_factual"].to_numpy().reshape(-1,1)
        data["ycf"] = dataset["y_cfactual"].to_numpy().reshape(-1,1)

        # If T == 0, then y_factual is y0 and y_cfactual is y1.
        # vice versa
        y0 = []
        y1 = []
        for i in range(len(dataset["treatment"])):
            if dataset["treatment"][i] == 0:
                y0.append([dataset["y_factual"][i]])
                y1.append([dataset["y_cfactual"][i]])
            else:
                y0.append([dataset["y_cfactual"][i]])
                y1.append([dataset["y_factual"][i]])
        data["y0"] = np.asarray(y0)
        data["y1"] = np.asarray(y1)

        # numpy array, each row is one instance, each column is one variable
        # i.e. data["X"][0] returns the all variables for the 0th patient
        x = dataset.iloc[:, 5:]
        data["x"] = x.to_numpy()

        # Record the label
        # data["x_label"] = np.array(col[5:])

        # Have to manually input this part based on prior knowledge
        # data["raw"] = {"T": 1, "Y0": 0, "Y1": 0, "Y": 1, "X": 1}
        return data


if __name__ == "__main__":
    num_batch = 190
    loader = format_processor()
    loader.load_data("TWINS")
    dct = loader.data
    # for index in range(len(dct["yf"])):
    #     print(dct["yf"][index], dct["ycf"][index])

    # Currently disabling pipeline to organize raw data
    # pipeline = Pipeline([('imputer', SimpleImputer()), ('scaler', Normalizer())])
    # dct = loader.data_processing(Y_transformer=StandardScaler(), X_transformer=pipeline)
    # print(dct)

    # reshape TWINS into batches
    dct_train = {}
    dct_test = {}
    idx = np.random.permutation(1140)
    train_rate = 0.9
    train_idx = idx[:int(train_rate * 1140)]
    test_idx = idx[int(train_rate * 1140):]
    for key, item in loader.data.items():
        if key == "x":

            dct_train[key] = item.reshape(-1, 30, 10)[train_idx,:,:]

            dct_test[key] = item.reshape(-1, 30, 10)[test_idx,:,:]
        else:
            dct_train[key] = item.reshape(-1, 10)[train_idx,:]
            dct_test[key] = item.reshape(-1, 10)[test_idx,:]
        # print("-----")
        print(key, dct[key].shape)
        print(key, dct_train[key].shape)
        print(key, dct_test[key].shape)


    # dct_train = {}
    # dct_test = {}
    # no = dct["x"].shape[0]
    # idx = np.random.permutation(no)
    # train_rate = 0.8
    # train_idx = idx[:int(train_rate * no)]
    # test_idx = idx[int(train_rate * no):]
    #
    # # reshape TWINS into batches
    # for key, item in loader.data.items():
    #     if key == "x":
    #         dct_train[key] = item[train_idx,:].reshape(-1, 30, 1)
    #
    #         dct_test[key] = item[test_idx,:].reshape(-1, 30, 1)
    #     else:
    #         dct_train[key] = item[train_idx].reshape(-1, 1)
    #         dct_test[key] = item[test_idx].reshape(-1,1)
    #     # print("-----")
    #     print(key, dct[key].shape)
    #     print(key, dct_train[key].shape)
    #     print(key, dct_test[key].shape)


    # reshape ihdp into batches
    # dct_train = {}
    # dct_test = {}
    # for key, item in loader.data.items():
    #     if key == "x":
    #         dct_train[key] = item.reshape(-1, 25, num_batch)[:,:,:80]
    #         dct_test[key] = item.reshape(-1, 25, num_batch)[:,:,80:]
    #     else:
    #         dct_train[key] = item.reshape(-1, num_batch)[:,:80]
    #         dct_test[key] = item.reshape(-1, num_batch)[:,80:]
    #     # print("-----")
    #     print(key, dct[key].shape)
    #     print(key, dct_train[key].shape)
    #     print(key, dct_test[key].shape)

    np.savez("../datasets/TWINS/twins_train", **dct_train)
    np.savez("../datasets/TWINS/twins_test", **dct_test)
    # x = np.load("../datasets/JOBS/jobs_DW_bin.train.npz")
    # x = np.load("../datasets/TWINS/twins_test_preprocessed.npz")
    # for key in x:
    #     print(key, x[key].shape)