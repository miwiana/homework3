

import requests
import json
import hashlib

class PeopleClientError(Exception):
    pass

class PeopleClient:

    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token

    def get_all(self):
        return requests.get(self.base_url).json()


    def get_all_param(self, limit = None):
        if limit is None:
            return requests.get(self.base_url).json()

        if limit <= 0 :
            raise ValueError("Limit has to be positive")

        response = requests.get(self.base_url, params={"_limit": limit})
        total = int(response.headers["X-Total-Count"])
        pages = total // limit

        if total % limit != 0:
            pages += 1

        people = response.json()

        for page in range(2, pages+1):
            chunk = requests.get(self.base_url, params={"_limit":limit, "_page":page}).json()
            people.extend(chunk)
        return people


    def add_person(self, first_name, last_name, email, phone, ip_address):
        headers = {"Authorization": "Bearer " + self.token}
        person =  {"first_name": first_name,
          "last_name": last_name,
          "email": email,
          "phone": phone,
          "ip_address": ip_address}
        response = requests.post(self.base_url, json=person, headers=headers)

        if response.status_code != 201:
            raise PeopleClientError(response.json()["error"])
        return response.json()

    def person_by_id(self, person_id):
        url = self.base_url + str(person_id)
        response = requests.get(url)
        if response.status_code == 404:
           raise PeopleClientError("User with given id not found")
        elif not response.ok:
            raise PeopleClientError(response.json()["Error"])
        return response.json()

    def query(self, **criteria):

        fields_names = ('first_name', 'last_name', 'email', 'phone', 'ip_address')

        for key, value in criteria.items():
            if key not in fields_names:
                raise ValueError("Nie ma takiego klucza: " + key)

        response = requests.get(self.base_url, params=criteria)
        return response.json()

    def people_by_partial_ip(self, partial_ip):

        reg_partial_ip = "^" + partial_ip
        response = requests.get(self.base_url, params={"ip_address_like":reg_partial_ip})
        return response.json()




    def delete_by_id(self, person_id):
        headers = {"Authorization": "Bearer " + self.token}
        url = self.base_url + str(person_id)
        response = requests.delete(url, headers=headers)
        if response.status_code == 404:
           raise PeopleClientError("Użytkownik o podanym ID nie istnieje")
        elif not response.ok:
            raise PeopleClientError(response.json()["Error"])
        return response.json()


    def delete_by_name(self, first_name):
        headers = {"Authorization": "Bearer " + self.token}
        response = requests.get(self.base_url, headers=headers, params={"first_name": first_name}).json()

        count = 0
        for dict in response:
            person_id = dict["id"]
            url = self.base_url + str(person_id)
            del_response = requests.delete(url, headers=headers)
            if del_response.status_code == 200:
                count += 1

        if len(response) == 0 :
            return "Nie znaleziono użytkownika o podanym imieniu"

        return "Usunięto " + str(count) + "/" + str(len(response)) + " użytkowników"


    def add_from_json_file(self, input_file):

        list_of_people = json.load(input_file)

        headers = {"Authorization": "Bearer " + self.token}
        list_of_responses = []

        for dict in list_of_people:
            response = requests.post(self.base_url, json=dict, headers=headers)

            if response.status_code != 201:
                raise PeopleClientError(response.json()["error"])
            list_of_responses.append(response.json())

        return list_of_responses


if __name__ == "__main__":

    token = hashlib.md5("relayr".encode("ascii")).hexdigest()
    client = PeopleClient("http://polakow.eu:3000/people/", token)

    print(client.delete_by_id("RHnJEzF"))
    print(client.delete_by_name("Geralt"))

    with open("my_file.json", "rt") as my_file:
        print(client.add_from_json_file(my_file))
