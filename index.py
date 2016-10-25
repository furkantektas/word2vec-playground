#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys,os,json
import urlparse
from optparse import OptionParser
from BaseHTTPServer import HTTPServer,BaseHTTPRequestHandler
import gensim # word2vec

class http_server:
    def __init__(self, model, port):
        def handler(*args):
            Word2VecHandler(model, *args)
        server = HTTPServer(('', port), handler)
        print 'Starting server at port {}, use <Ctrl-C> to stop'.format(port)
        server.serve_forever()

class Word2VecHandler(BaseHTTPRequestHandler):
    def __init__(self,model,*args):
        self.model = model
        BaseHTTPRequestHandler.__init__(self, *args)
    def jsonResponse(self,content):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(content))
    def do_GET(self):
        try:
            if self.path.startswith('/analogy'):
                parsed_path = urlparse.urlparse(self.path)
                pos_words = urlparse.parse_qs(urlparse.urlparse(self.path).query).get('pos_words[]', None)
                neg_word = urlparse.parse_qs(urlparse.urlparse(self.path).query).get('neg_word', None)
                similars = self.model.most_similar(positive=pos_words, negative=neg_word)
                self.jsonResponse(similars)
                return
            elif self.path.startswith('/similarity'):
                parsed_path = urlparse.urlparse(self.path)
                sim_words = urlparse.parse_qs(urlparse.urlparse(self.path).query).get('sim_words[]', None)
                score = 0
                if len(sim_words) == 2:
                    score = self.model.similarity(sim_words[0],sim_words[1])
                self.jsonResponse(score)
                return
            elif self.path.startswith('/most_similar'):
                parsed_path = urlparse.urlparse(self.path)
                word = urlparse.parse_qs(urlparse.urlparse(self.path).query).get('sim_word', None)[0]
                scores = self.model[word]
                similarWords = self.model.similar_by_word(word, topn=10)
                self.jsonResponse(similarWords)
                return
            elif self.path == '/':
                f = open('index.html')
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
        except IOError:
          self.send_error(404, 'file not found')

def printUsage():
    print 'Usage: index.py -m <modelfile> [-b]'

def main(argv):
    parser = OptionParser()
    parser.add_option("-m", "--model", dest="model",
                      help="uncompressed word2vec model")
    parser.add_option("-b", "--binary",
                      action="store_true", dest="isBinary", default=False,
                      help="is word2vec model binary")
    parser.add_option("-p", "--port",
                      type="int", dest="port", default=8080,
                      help="server port")
    (options, args) = parser.parse_args()

    if not os.path.isfile(options.model):
        parser.error("You should specify model file.")

    from BaseHTTPServer import HTTPServer
    model = gensim.models.Word2Vec.load_word2vec_format(options.model,
        binary=options.isBinary)
    model.init_sims(replace=True)
    print 'Model loaded.'
    server = http_server(model,options.port)

if __name__ == "__main__":
    main(sys.argv[1:])
