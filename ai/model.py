import os.path
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

from ai.early_stopper import EarlyStopper


class WeightCalculatorAI(nn.Module):
    #(0.1 for validation(how many epochs), 0.1 for test, 0.8 for training, learning rate - size of steps (to decrease loss), weight decay to decrease learning rate (smaller steps)
    def __init__(self, dim:int=0, parameters_location:str='parameters.csv', T=None, lr=0.005, weight_decay=5e-4, path='ai_weights', dtype=torch.float, train_test_split=(0.8, 0.1, 0.1), load=False):
        super().__init__()
        self.parameters_location = parameters_location
        self.dim = dim

        # Path to save the model weights
        if 'ai' in os.listdir('.'): # If it gets called from GUI
            path = 'ai' + path
        self.path = path + '/weights.pth'
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

        self.dtype = dtype
        self.train_test_split = train_test_split
        self.thresh_nominator, self.thresh_denominator = (torch.tensor(T[0], dtype=self.dtype), torch.tensor(T[1], dtype=self.dtype)) if T is not None else (None, None)
        #first time instantiation (11 random weights)
        random_weights_from_gauss_distr = torch.rand(self.dim, dtype=self.dtype)
        self.W = nn.Parameter(random_weights_from_gauss_distr, requires_grad=True)


        self.optimizer = torch.optim.Adam(self.parameters(), lr=lr, weight_decay=weight_decay)
        self.loss_fn = nn.MSELoss()
        if load:
            self.load_model()

    def forward(self, S):
        x = torch.log(1 + torch.maximum(S, self.thresh_nominator)) / torch.log(1 + torch.maximum(S, other=self.thresh_denominator))
        y = (x @ self.W) / torch.sum(torch.abs(self.W))
        return y

    def save_model(self):
        df = pd.read_csv(self.parameters_location)
        if 'weight_ai' not in df.keys():
            raise KeyError("AI weights column not in the parameters file!")

        df['weight_ai'] = pd.Series(self.get_weights())
        df.to_csv(self.parameters_location, index=False)
        torch.save(self.state_dict(), self.path)

    def load_model(self):
        #load_state_dict svi parametri se ucitaju iz oth filea u samog sebe
        self.load_state_dict(torch.load(self.path))

    def get_weights(self):
        weights = self.W.detach().numpy()
        #to get a new nice interval [0,10]
        weights = (weights - weights.min()) / (weights.max() - weights.min()) * 10
        weights = weights.round(2)
        return weights

    def fit(self, data, epochs=50, batch_size=64, verbose=True, es_patience=5, es_min_delta=0, progress_bar=None, master_frame=None):
        #training
        # Reinitialize weights
        self.W = nn.Parameter(torch.rand(self.dim, dtype=self.dtype), requires_grad=True)

        # Parse data
        data = torch.from_numpy(data.to_numpy()).to(self.dtype)

        train_size = int(self.train_test_split[0] * len(data))
        valid_size = int(self.train_test_split[1] * len(data))

        if train_size == 0 or valid_size == 0:
            raise Exception("Dataset is too small with this split! Train/valid loader is of lenght 0.")

        train_set = TensorDataset(data[:train_size, :-1], data[:train_size, -1])
        valid_set = TensorDataset(data[train_size:(train_size+valid_size), :-1], data[train_size:(train_size+valid_size), -1])

        #DataLoader koristimo zbog batcheva
        train_loader = DataLoader(train_set, shuffle=True, batch_size=batch_size)
        valid_loader = DataLoader(valid_set, shuffle=True, batch_size=batch_size)

        # Train the model
        train_loss_history = []
        valid_loss_history = []

        self.train() # Tell the model you are in train mode
        early_stopper = EarlyStopper(patience=es_patience, min_delta=es_min_delta)
        for epoch in range(epochs):
            # Train loop
            train_losses = []
            for X_batch, labels in train_loader:
                prediction = self(X_batch)
                loss = self.loss_fn(prediction, labels)
                train_losses.append(loss.item())

                # Optimization of weights
                self.optimizer.zero_grad() # Set all gradients of the model to zero
                loss.backward() # Backpropagate through the model to calculate the new gradients
                self.optimizer.step() # Update the weights of the model with new gradients
            train_loss_history.append(sum(train_losses) / len(train_losses))

            # Validation loop
            valid_losses = []
            for X_batch, labels in valid_loader:
                prediction = self(X_batch)
                loss = self.loss_fn(prediction, labels)
                valid_losses.append(loss.item())
            valid_loss_history.append(sum(valid_losses) / len(valid_losses))

            # Track progress
            if verbose:
                print(f"Epoch {epoch+1}/{epochs} | Train Loss: {train_loss_history[-1]} | Valid Loss: {valid_loss_history[-1]}")
            # Update progress if running from GUI
            if progress_bar:
                progress_bar['value'] = (epoch+1)/epochs*100
                if master_frame:
                    master_frame.update_idletasks()

            # Check for early stopping
            es_flag = early_stopper.early_stop(valid_loss_history[-1])
            if es_flag == 1: # izgubia je strpljenje jer je zadnjih 5 epoha gori nego sta je bia prije
                if verbose:
                    print("Early stopping!")
                #it loads the last best model (saved by elif)
                self.load_model()
                break
            elif es_flag == 3: #vraca 3 dok se model poboljsava, validation set pravac se smanjuje (moze vracat i 2, to je kad se pogorsava ali nije proslo 5 epoha)
                #keeps saving to pth while validation loss is decreasing
                self.save_model()


    def evaluate(self, data, batch_size=64, verbose=True):
        # Dajemo set od 10% za test
        data = torch.from_numpy(data.to_numpy()).to(self.dtype)
        test_size = int(self.train_test_split[2] * len(data))
        # test_set = x(od zadnjih 10% bez zadnjeg stupca (rezultat)) , y(zadnjih 10 posto samo zadnji stupac)
        test_set = TensorDataset(data[-test_size:, :-1], data[-test_size:, -1])
        test_loader = DataLoader(test_set, shuffle=True, batch_size=batch_size)

        # Test model
        losses = []
        self.eval() # Tell the model you are in eval mode
        with torch.no_grad():
            #batch = 64*11, label = pravi y
            for X_batch, labels in test_loader:
                prediction = self(X_batch) # poziva forward
                loss = self.loss_fn(prediction, labels)
                losses.append(loss.item())
        loss_eval = sum(losses) / len(losses)

        # Print loss
        if verbose:
            print(f"Evaluation loss: {loss_eval}")

        return loss_eval

