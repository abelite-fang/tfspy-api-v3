import json

my_list = [{"name": "resnet","base_path": "/notebooks/train-data/ResNet-50v2","model_platform": "tensorflow","version": "1538687370"}]
ststr = json.dumps(my_list)

with open('config.json', 'wt') as f:
    f.write(ststr)
    print("finished")

with open('config.json','rt') as f:
    data = json.load(f)
    print(data)
