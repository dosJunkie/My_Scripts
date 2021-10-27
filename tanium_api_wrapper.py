import requests
import json
import datetime as dt

class TaniumApiWrapper():


    def __init__(self):
        self.base_url = "https://jsonplaceholder.typicode.com/posts/"

    def show_post(self, id):
        """This method takes in an id argument and returns a
        json object back, but only if the request has a
        successful status code of 200."""
        url = f'{self.base_url}{id}'
        r = requests.get(url=url)
        status = r.status_code

        if status == 200:
            data = r.json()
            data["status"] = status
            return data
        else:
            error = {
                    "error":"Sorry! The request was not successful.", 
                    "status":status
                    }
            return error

    def deliver_time(self, id):
        """This method calls the show_post method with an id 
        argument and simply adds in a key to the json object. 
        The key is named time and the value will be the exact 
        time in UTC that the function was called. The json 
        object is then returned."""
        response = self.show_post(id)
        utc = dt.datetime.now(dt.timezone.utc).strftime("%d/%m/%Y %H:%M:%S")
        response.update(time=utc)
        return response

    def create_post(self, obj):
        """This method takes takes in a mandatory dictionary/json 
        object and creates a post on the given API endpoint. If 
        the POST is successful then a dictionary is passed with 3 pieces of data.""" 
        if not isinstance(obj, dict):
            return "Please format object into a Python dictionary."

        url = self.base_url
        r = requests.post(url=url, data=obj)

        data = r.json()
        status = r.status_code
        headers = r.headers["x-Powered-By"]

        if status == 200 or 201:
            return {"status": status, "headers":headers, "data":data}
        else:
            error = {
                    "error":"Sorry! The POST was not successful.",
                    "status":status
                    }
            return error

    def delete_post(self, id):
        """This method takes in an id argument and sends a delete
        request to that given endpoint. If the request is successful
        then a dictionary object with 2 values are returned."""
        url = f'{self.base_url}{id}'
        r = requests.delete(url=url)
        status = r.status_code
        headers = r.headers["X-Content-Type-Options"]

        if status == 200:
            return_info = {"status":status, "X-Content":headers}
            return return_info
        else:
            error = {
                    "error":"Sorry! The request was not successful.",
                    "status":status
                    }
            return error