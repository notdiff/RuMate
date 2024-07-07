import yandex_search
import mistral_search
import search_agents
import parce
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route('/searched_info', methods=['GET'])
def search_info():
    query = request.args.get('query')
    model = request.args.get('model', default='yandex')

    if model == 'mistral':
        search_res = mistral_search.refactor_llm_ans(query)
    else:
        search_res = yandex_search.refactor_sim_search_res(query)

    ans = {'reply': search_res}

    return jsonify(ans)


@app.route('/agents', methods=['GET'])
def agents():
    query = request.args.get('query')

    search_res = search_agents.get_agents_res(query)
    ans = {'reply': search_res}

    return jsonify(ans)


@app.route('/parse', methods=['GET'])
def agents():

    parce.main()

    return {'success': True}


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        debug=True
        )