import os
count = 0
for filename in os.listdir("C:/train_data/"):
    new_file_name = "13.10.2023_1_{0}.{1}".format(count, filename.split('.')[-1])
    os.rename("C:/train_data/{0}".format(filename), "C:/train_data/{0}".format(new_file_name))
    count = count + 1
print("Done!")