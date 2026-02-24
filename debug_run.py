from app import app

if __name__ == '__main__':
    print('Starting debug server on port 5001')
    app.run(host='127.0.0.1', port=5001, debug=True, use_reloader=False)
