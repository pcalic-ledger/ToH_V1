#from configparser import SafeConfigParser
import os
#from pickletools import float8
from urllib import request
import creator as cr
import matplotlib.pyplot as plt
import numpy as np

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torch.nn.functional as F


from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request


def create_app(test_config=None):
    #create and config the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY = 'calic',
        DATABASE = os.path.join(app.instance_path, 'flaskr.sqlite')
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent = True)
    else: 
        app.config.from_mapping(test_config)    

    #test existence
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    #For storing responses later
    user_response = np.empty([84,84])
    
    class Net(nn.Module):
        def __init__(self):
            super(Net, self).__init__()
            self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
            self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
            self.conv2_drop = nn.Dropout2d()
            self.fc1 = nn.Linear(320, 50)
            self.fc2 = nn.Linear(50, 10)

        def forward(self, x):
            x = F.relu(F.max_pool2d(self.conv1(x), 2))
            x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
            x = x.view(-1, 320)
            x = F.relu(self.fc1(x))
            x = F.dropout(x, training=self.training)
            x = self.fc2(x)
            return F.log_softmax(x)        
     
    
    # Load
    model = Net()
    model.load_state_dict(torch.load("model.pth"))
    model.eval()
    
    def captcha(prediction,target):
        if (prediction == target):
            return True
        else:
            return False



    #routing
    @app.route('/img_array', methods = ['GET'])
    def serveArray():
        LI = cr.retImGrid()
        a = 3     #Make it a Random Number
        return jsonify(array=LI, num=a)             #send question also

    
    
    @app.route('/snap_array', methods = ['POST'])
    def snapArray():
        data = request.json                  #retrieve question also
        dataList = list(data['data'].values())
        datanp = np.array(dataList)
        
        #First lets remove every 4th elemnnt from the vector
        datanp = np.delete(datanp, np.arange(0, datanp.size, 4))
        datanp = datanp.reshape(84,84,3)

        for i in range(84):
            for j in range(84):
                user_response[i][j] = datanp[i][j][0]                                     

        #convert to format ready to jump in the classifier
        
        user_response_GrayNP = user_response/255.0
        user_response_GrayNP = cr.resizeIm(user_response_GrayNP, 100/3)
        user_response_GrayNP = user_response_GrayNP.astype(np.float32)
        
        example = torchvision.transforms.ToTensor()(user_response_GrayNP)
        
        output = model(example)     #produces the output
        pred = output.data.max(1, keepdim=True)[1]    
        #the answer to the test
        test_evalution = captcha(pred.item(),3) 

        return jsonify(test_evalution)        

    @app.route('/')
    def index():
        return render_template("index.html")
    
    @app.route('/about')
    def about():
        return "Internship at ledger 2022, AI Master student at UPMC"

    return app
