from flask import Flask, request, jsonify, Response


app = Flask(__name__)
'''
@app.route('/<uuid>', methods=["GET","POST"])
def index(uuid):
    content = request.json
    print content['mytext']
    return jsonify({"uuid":uuid})
'''

@app.route('/<args>')
def index(args):
    data = {"fruits":"apple", "vegitable":"carrot"}
    return Response(json.dumps(data), mimetype="application/json")

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
