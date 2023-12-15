from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from mysql.connector import Error
from mysql_connection import get_connection

class FollowResource(Resource) :
    # 친구 맺기
    @jwt_required()
    def post(self) :

        followeeId = request.args.get("followeeId")
        user_id = get_jwt_identity()
        
        if followeeId == user_id :
            return {"error" : "자기 자신과는 친구할 수 없습니다."}, 400
        
        try :
            connection = get_connection()

            query = '''
                    insert into follow
                    (followerId, followeeId)
                    values
                    (%s, %s);
                    '''
            record = (user_id, followeeId)
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"result" : "fail", "error" : str(e)}, 500

        return {"result" : "success"}, 200
    
    # 친구 끊기
    @jwt_required()
    def delete(self) :
        
        followeeId = request.args.get("followeeId")
        user_id = get_jwt_identity()

        try :
            connection = get_connection()

            query ='''
                    delete from follow
                    where followerId = %s and followeeId = %s;
                    '''
            record = (user_id, followeeId)
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"result" : "fail", "error" : str(e)}, 500
        
        return {"result" : "success"}, 200

class FollowPostingResourece(Resource) :
    # 내 친구 포스팅만 보기
    @jwt_required()
    def get(self) :

        user_id = get_jwt_identity()

        offset = request.args.get("offset")
        limit = request.args.get("limit")

        try :
            connection = get_connection()

            query = '''
                    select i.*, count(fa.id) as favoriteCnt, if(fa.userId = 1, 1, 0) as favoriteOx 
                    from user u
                    join follow f
                    on u.id = f.followerId
                    join image i
                    on f.followeeId = i.userId
                    left join favorite fa
                    on i.id = fa.imageId
                    where u.id = %s
                    group by i.id
                    order by i.createdAt desc
                    limit ''' + offset + ''', ''' + limit + ''';
                    '''
            
            record = (user_id, )

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            result_list = cursor.fetchall()

            i = 0
            for row in result_list :
                result_list[i]["createdAt"] = row["createdAt"].isoformat()
                i = i+1

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"result" : "fail", "error" : str(e)}, 500

        if len(result_list) == 0 :
            return {"error" : "포스팅된 글이 없습니다."}, 400

        return {"result" : "success", "items" : result_list, "count" : len(result_list)}, 200
