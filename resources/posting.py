from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from config import Config
from mysql_connection import get_connection
from mysql.connector import Error
from datetime import datetime
import boto3

# 포스팅 하기
class PostingListResource(Resource) :
    @jwt_required()
    def post(self) :

        file = request.files.get("photo")
        content = request.form.get("content")
        user_id = get_jwt_identity()

        if file is None :
            return {"error" : "파일이 없습니다."}, 400
        
        current_time = datetime.now()

        new_file_name = current_time.isoformat().replace(":", "_") + str(user_id) + ".jpg"

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
        
        # rekognition 서비스를 이용해서 object detection 하여,
        # 태그 이름을 가져온다.

        tag_list = self.detect_labels(new_file_name, Config.S3_BUCKET)

        # DB의 posting 테이블에 데이터를 넣어야 하고,
        # tag_name 테이블과 tag 테이블에도 데이터를 넣어줘야 한다.

        try :
            connection = get_connection()

            query = '''
                    insert into image
                    (userId, imageUrl, content)
                    values
                    (%s, %s, %s);
                    '''
            
            imgUrl = Config.S3_LOCATION + new_file_name

            record = (user_id, imgUrl, content)

            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()

            cursor.close()
            connection.close()

        except Exception as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500

        return {"result" : "success", "imgUrl" : imgUrl}, 200
    
    def detect_labels(self, photo, bucket) :

        client = boto3.client('rekognition', 'ap-northeast-2', 
                              aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY)

        response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}},
                                        
        MaxLabels=5,
        # Uncomment to use image properties and filtration settings
        #Features=["GENERAL_LABELS", "IMAGE_PROPERTIES"],
        #Settings={"GeneralLabels": {"LabelInclusionFilters":["Cat"]},
        # "ImageProperties": {"MaxDominantColors":10}}
        )

        print('Detected labels for ' + photo)
        print()

        label_list = []
        for label in response['Labels']:
            print("Label: " + label['Name'])
            print("Confidence: " + str(label['Confidence']))

            if (label['Confidence']) >= 90 :
                label_list.append(label['Name'])

        return label_list