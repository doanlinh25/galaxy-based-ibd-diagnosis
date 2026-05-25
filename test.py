# import random as rd
# from io import BytesIO
# from json import load
#
# import boto3
# import botocore
#
# from ML.mainml import load_data, prepare_data, train_rf_model, visualize_model_results
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import accuracy_score
# from DataPreprocessing.cleaned_data import process_folder_r2, merge_label_r2
#
# s3_client = boto3.client(
#         's3',
#         endpoint_url="https://d63681a062448ae7aa50388acf0ee16f.r2.cloudflarestorage.com/",
#         aws_access_key_id="e13229540b5d1188b0aabae2ab1741c0",
#         aws_secret_access_key="b21fed7924f5e4e654321289e7b48022c956774fd8b51ac109a606a149e73edb",
#         config=botocore.client.Config(signature_version='s3v4'),
#         verify=False
# )
# # train_rf_model()
# # key_model = "models/rf_model.joblib"
# # obj = s3_client.get_object(Bucket="ppnckh", Key=key_model)
# # buffer = BytesIO(obj['Body'].read())
# # model = load(buffer)
#
# # # process_folder_r2()
# # # merge_label_r2(s3_client, "ppnckh")
# #
# # df = load_data(path_file=r"C:\Users\User\ppnckh\cleaned_data\wf0\r2\merged.csv")
# # # print(list(df.columns)[::-1])
# # X, y = prepare_data(df,0)
# #
# # # Train / test split
# # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
# # acc = 0
# # while True:
# #     # Khởi tạo model
# #     model = RandomForestClassifier(n_estimators=200, random_state=rd.randint(600, 700))
# #
# #     # Huấn luyện
# #     model.fit(X_train, y_train)
# #
# #     # Dự đoán
# #     y_pred = model.predict(X_test)
# #
# #     # Đánh giá
# #     acc = accuracy_score(y_test, y_pred)
# #     print("Accuracy:", acc)
# #     if acc > 0.75:
# #         break