# -*- coding: utf-8 -*-

from flask import Flask
from flask_restful import Resource, Api
from sqlalchemy import create_engine

eng = create_engine('sqlite:///static/trafi.db')
app = Flask(__name__)
api = Api(app)
 
class HybridsByCity(Resource):
    def get(self, city):
        conn = eng.connect()
        query = conn.execute('SELECT * FROM hybrids \
                             WHERE kuntanimi="{}"'.format(city))
        result = {'data': [dict(zip(tuple(query.keys()), i)) for 
                           i in query.cursor]}
        return(result)

class HybridsByCityAndYear(Resource):
    def get(self, city, year):
        conn = eng.connect()
        query = conn.execute('SELECT * FROM hybrids \
                             WHERE kuntanimi="{}" AND \
                             kayttoonottopvm LIKE "{}%"'.format(
                             city, year))
        result = {'data': [dict(zip(tuple(query.keys()), i)) for 
                           i in query.cursor]}
        return(result)
        
@app.route('/')
def health():
    html = """Service up. Fetch data on hybrid vehicles registered 
	in Finland by <a href="/utsjoki">city</a> and registration 
    <a href="/helsinki/2005">year</a>."""
    return(html)


api.add_resource(HybridsByCity, '/<string:city>')
api.add_resource(HybridsByCityAndYear, '/<string:city>/<string:year>')

if __name__ == '__main__':
     app.run(port=8080)
