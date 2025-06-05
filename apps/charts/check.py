import torch
model_path = "E:/ĐHBKĐN/BKĐN-Năm 4, Học kì 2/PBL7/PBL7_Main/apps/charts/models/13_05_lstm_job_forecast.h5"
obj = torch.load(model_path, weights_only=False)
print(type(obj))