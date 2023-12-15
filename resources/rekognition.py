from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from config import Config
from mysql_connection import get_connection
from mysql.connector import Error
from datetime import datetime
import boto3

# 이미지 분석
class ObjectDetectionResource(Resource) :
    @jwt_required()
    def post(self) :

        file = request.files.get("photo")

        if file is None :
            return {"error" : "파일이 존재하지 않습니다."}, 400
        
        current_time = datetime.now()

        new_file_name = current_time.isoformat().replace(":", "_") + ".jpg"

        file.filename = new_file_name

        s3 = boto3.client("s3", aws_access_key_id = Config.AWS_ACCESS_KEY_ID,
                     aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY)

        try :
            s3.upload_fileobj(file, Config.S3_BUCKET, file.filename, 
                              ExtraArgs = {"ACL" : "public-read",
                                           "ContentType" : "image/jpeg"})

        except Exception as e :
            print(e)
            return {"error" : str(e)}, 500
        
        # S3에 이미지가 있으니 rekognition 이용해서 object detection 한다.

        label_list = self.detect_labels(new_file_name, Config.S3_BUCKET)
        
        return {"result" : "success", "labels" : label_list, "count" : len(label_list)}, 200
    
    def detect_labels(self, photo, bucket) :

        client = boto3.client('rekognition', 'ap-northeast-2', 
                              aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY)

        response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}},
        
        MaxLabels=10,
        # Uncomment to use image properties and filtration settings
        #Features=["GENERAL_LABELS", "IMAGE_PROPERTIES"],
        #Settings={"GeneralLabels": {"LabelInclusionFilters":["Cat"]},
        # "ImageProperties": {"MaxDominantColors":10}}
        )

        print('Detected labels for ' + photo)
        print()
        for label in response['Labels']:
            print("Label: " + label['Name'])
            print("Confidence: " + str(label['Confidence']))
            print("Instances:")

            for instance in label['Instances']:
                print(" Bounding box")
                print(" Top: " + str(instance['BoundingBox']['Top']))
                print(" Left: " + str(instance['BoundingBox']['Left']))
                print(" Width: " + str(instance['BoundingBox']['Width']))
                print(" Height: " + str(instance['BoundingBox']['Height']))
                print(" Confidence: " + str(instance['Confidence']))
                print()

            print("Parents:")
            for parent in label['Parents']:
                print(" " + parent['Name'])

            print("Aliases:")
            for alias in label['Aliases']:
                print(" " + alias['Name'])

                print("Categories:")
            for category in label['Categories']:
                print(" " + category['Name'])
                print("----------")
                print()

        if "ImageProperties" in str(response):
            print("Background:")
            print(response["ImageProperties"]["Background"])
            print()
            print("Foreground:")
            print(response["ImageProperties"]["Foreground"])
            print()
            print("Quality:")
            print(response["ImageProperties"]["Quality"])
            print()

        return response['Labels']