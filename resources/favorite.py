from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from mysql.connector import Error
from mysql_connection import get_connection

# 좋아요
class FavoriteResource(Resource) :
    # 좋아요 추가
    @jwt_required()
    def post(self, favoriteId) :

        user_id = get_jwt_identity()

        try :
            connection = get_connection()

            query = '''
                    insert into favorite
                    (userId, postingId)
                    values
                    (%s, %s);
                    '''
            
            record = (user_id, favoriteId)

            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500
        
        return {"result" : "success"}, 200
    
    # 좋아요 삭제
    @jwt_required()
    def delete(self, favoriteId) :

        user_id = get_jwt_identity()

        try :
            connection = get_connection()

            query = '''
                    delete from favorite
                    where userId = %s and postingId = %s;
                    '''
            
            record = (user_id, favoriteId)

            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500
        
        return {"result" : "success"}, 200