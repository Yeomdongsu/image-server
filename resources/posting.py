from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from config import Config
from mysql_connection import get_connection
from mysql.connector import Error
from datetime import datetime
import boto3

# 포스팅 하기
class PostingResource(Resource) :
    @jwt_required()
    def post(self) :

        file = request.files.get("photo")
        content = request.form.get("content")
        user_id = get_jwt_identity()

        if file is None :
            return {"error" : "파일이 없습니다."}, 400
        
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