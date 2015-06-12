__author__ = 'Markus Ackermann <ackermann@uni-leipzig.de>'

from sys import argv
from os import environ
from rdflib import Graph, Literal, URIRef, Namespace

CONF = Namespace("http://richard.cyganiak.de/2007/pubby/config.rdf#")
PLACEHOLDER = Namespace("urn:placeholder#")


class ConfigurationItem:
    def __init__(self, env_var, conf_prop, placeholder_res, default_val):
        self._env_var = env_var
        self._conf_prop = conf_prop
        self._placeholder_res = placeholder_res
        self._default_val = default_val

    @property
    def env_var(self):
        return self._env_var

    @property
    def conf_prop(self):
        return self._conf_prop

    @property
    def placeholder_res(self):
        return self._placeholder_res

    @property
    def default_value(self):
        return self._default_val


CONFIG_ITEMS = [
    ConfigurationItem("STORE_SPARQL_ENDPOINT_URL", CONF.sparqlEndpoint,
                      PLACEHOLDER.sparqlEndpoint, URIRef("http://localhost:8890/sparql/")),
    ConfigurationItem("STORE_MAIN_GRAPH", CONF.sparqlDefaultGraph,
                      PLACEHOLDER.sparqlDefaultGraph, URIRef("http://dbpedia.org")),

    ConfigurationItem("PROJECT_NAME", CONF.projectName,
                      PLACEHOLDER.projectName, Literal("Dockerized Pubby")),
    ConfigurationItem("PROJECT_HOMEPAGE", CONF.projectHomepage,
                      PLACEHOLDER.projectHomepage, URIRef("http://wiki.dbpedia.org")),
    ConfigurationItem("INDEX_RESOURCE", CONF.indexResource,
                      PLACEHOLDER.indexResource, URIRef('http://dbpedia.org/resource/Wikipedia')),
    ConfigurationItem("DATASET_BASE", CONF.datasetBase,
                      PLACEHOLDER.datasetBase, URIRef("http://dbpedia.org/resource/")),
    ConfigurationItem("WEB_BASE", CONF.webBase,
                      PLACEHOLDER.webBase, URIRef("http://localhost:8080/"))
]

class PubbyReconfiguration:
    def __init__(self, template_graph):
        self.config = template_graph
        self.base = self._find_base()

    def _find_base(self):
        subjects = set(self.config.subjects())
        file_subj = [str(f) for f in subjects if str(f).startswith('file://')]
        if len(file_subj) == 1:
            return file_subj[0]
        else:
            raise RuntimeError("cannot find @base resource equivalent ({len} results: {res})"
                               .format(len=len(file_subj), res=file_subj))

    def insert_values(self):
        for config_item in CONFIG_ITEMS:
            try:
                env_val = environ[config_item.env_var]
                type_converter = type(config_item.default_value)
                subs_obj = type_converter(env_val)
            except KeyError:
                subs_obj = config_item.default_value

            for placeholder_triple in \
                    self.config.triples((None, config_item.conf_prop, config_item.placeholder_res)):
                (subj, pred, o) = placeholder_triple
                self.config.add((subj, pred, subs_obj))
                self.config.remove(placeholder_triple)


if __name__ == '__main__':
    src_file = argv[1]
    target_file = argv[2]

    template_graph = Graph().parse(src_file, format='turtle')

    reconf = PubbyReconfiguration(template_graph)

    reconf.insert_values()
    reconf.config.serialize(target_file, format='turtle', base=reconf.base)
