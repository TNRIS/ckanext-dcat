import logging
import uuid

from pylons import config

from ckan import model

log = logging.getLogger(__name__)


CONTENT_TYPES = {
    'rdf': 'application/rdf+xml',
    'xml': 'application/rdf+xml',
    'n3': 'text/n3',
    'ttl': 'text/turtle',
    'jsonld': 'application/ld+json',
}


def catalog_uri():
    '''
    Returns an URI for the whole catalog

    This will be used to uniquely reference the CKAN instance on the RDF
    serializations and as a basis for eg datasets URIs (if not present on
    the metadata).

    The value will be the first found of:

        1. The `ckanext.dcat.base_uri` config option (recommended)
        2. The `ckan.site_url` config option
        3. `http://` + the `app_instance_uuid` config option (minus brackets)

    A warning is emited if the third option is used.

    Returns a string with the catalog URI.
    '''

    uri = config.get('ckanext.dcat.base_uri')
    if not uri:
        uri = config.get('ckan.site_url')
    if not uri:
        app_uuid = config.get('app_instance_uuid')
        if app_uuid:
            uri = 'http://' + app_uuid.replace('{', '').replace('}', '')
            log.critical('Using app id as catalog URI, you should set the ' +
                         '`ckanext.dcat.base_uri` or `ckan.site_url` option')
        else:
            uri = 'http://' + str(uuid.uuid4())
            log.critical('Using a random id as catalog URI, you should set ' +
                         'the `ckanext.dcat.base_uri` or `ckan.site_url` ' +
                         'option')

    return uri


def dataset_uri(dataset_dict):
    '''
    Returns an URI for the dataset

    This will be used to uniquely reference the dataset on the RDF
    serializations.

    The value will be the first found of:

        1. The value of the `uri` field
        2. The value of an extra with key `uri`
        3. `catalog_uri()` + '/dataset/' + `id` field

    Check the documentation for `catalog_uri()` for the recommended ways of
    setting it.

    Returns a string with the dataset URI.
    '''

    uri = dataset_dict.get('uri')
    if not uri:
        for extra in dataset_dict.get('extras', []):
            if extra['key'] == 'uri':
                uri = extra['value']
                break
    if not uri and dataset_dict.get('id'):
        uri = '{0}/dataset/{1}'.format(catalog_uri().rstrip('/'),
                                       dataset_dict['id'])
    if not uri:
        uri = '{0}/dataset/{1}'.format(catalog_uri().rstrip('/'),
                                       str(uuid.uuid4()))
        log.warning('Using a random id for dataset URI')

    return uri


def resource_uri(resource_dict):
    '''
    Returns an URI for the resource

    This will be used to uniquely reference the resource on the RDF
    serializations.

    The value will be the first found of:

        1. The value of the `uri` field
        2. `catalog_uri()` + '/dataset/' + `package_id` + '/resource/' + `id` field

    Check the documentation for `catalog_uri()` for the recommended ways of
    setting it.

    Returns a string with the resource URI.
    '''

    uri = resource_dict.get('uri')
    if not uri:
        dataset_id = dataset_id_from_resource(resource_dict)

        uri = '{0}/dataset/{1}/resource/{2}'.format(catalog_uri().rstrip('/'),
                                                    dataset_id,
                                                    resource_dict['id'])

    return uri


def publisher_uri_from_dataset_dict(dataset_dict):
    '''
    Returns an URI for a dataset's publisher

    This will be used to uniquely reference the publisher on the RDF
    serializations.

    The value will be the first found of:

        1. The value of the `publisher_uri` field
        2. The value of an extra with key `publisher_uri`
        3. `catalog_uri()` + '/organization/' + `organization id` field

    Check the documentation for `catalog_uri()` for the recommended ways of
    setting it.

    Returns a string with the publisher URI, or None if no URI could be
    generated.
    '''

    uri = dataset_dict.get('pubisher_uri')
    if not uri:
        for extra in dataset_dict.get('extras', []):
            if extra['key'] == 'publisher_uri':
                uri = extra['value']
                break
    if not uri and dataset_dict.get('organization'):
        uri = '{0}/organization/{1}'.format(catalog_uri().rstrip('/'),
                                            dataset_dict['organization']['id'])

    return uri


def dataset_id_from_resource(resource_dict):
    '''
    Finds the id for a dataset if not present on the resource dict
    '''
    dataset_id = resource_dict.get('package_id')
    if dataset_id:
        return dataset_id

    # CKAN < 2.3
    resource = model.Resource.get(resource_dict['id'])
    if resource:
        return resource.get_package_id()


def url_to_rdflib_format(_format):
    '''
    Translates the RDF formats used on the endpoints to rdflib ones
    '''
    if _format == 'ttl':
        _format = 'turtle'
    elif _format in ('rdf', 'xml'):
        _format = 'pretty-xml'
    elif _format == 'jsonld':
        _format = 'json-ld'

    return _format


def rdflib_to_url_format(_format):
    '''
    Translates RDF formats used by rdflib to the ones used on the endpoints
    '''
    if _format == 'turtle':
        _format = 'ttl'
    elif _format == 'pretty-xml':
        _format = 'xml'
    elif _format == 'json-ld':
        _format = 'jsonld'

    return _format