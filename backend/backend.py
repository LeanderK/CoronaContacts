from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse#, fields, marshal
from flask_restful import marshal, marshal_with
from flask_httpauth import HTTPBasicAuth
from webargs import fields, validate
from webargs.flaskparser import use_args
from datetime import datetime
import json

app = Flask(__name__, static_url_path="")
api = Api(app)
auth = HTTPBasicAuth()


@auth.get_password
def get_password(username):
    if username == 'test':
        return 'test'
    return None


@auth.error_handler
def unauthorized():
    # return 403 instead of 401 to prevent browsers from displaying the default
    # auth dialog
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)

example_contact = {
    'id': 1,
    # personal info
    'name': "Hans",
    'surname': "Wurst",
    'birthdate': datetime.fromisoformat("1939-05-08"),
    'street': "Kleine Straße 4",
    'zipcode': 00000,
    'place': "Nirgendwo",
    'telephone_numbers': ["099/987654321"],
    'risk_group': {
        'heart': True,
        'lung': False,
        'chronic_liver': False,
        'diabetis': True,
        'cancer': False,
        'weak_immunsystem': False,
    },
    'comment_availability': "nachmittags",
    #case information
    'exposing_case_comment': "unbekannt",
    'exposing_case_place': "Ausland",
    'status_case': 1, #Status Falltyp
    'symptons_begin': "2020-01-15",
    'infectious_begin': "2020-01-13", #anfang infektionszeitraum
    'infectious_end': "2020-01-25", #ende infektionszeitraum
    'is_contact_person': False,
    'state': "VZ",
    'reporting_district': "Kreis A", #meldelandkreis
    'gender': "männlich",
    'measures': [{
        'measure': "auf Isolierstation",
        'date': "2020-01-16"
    }]
}

contacts = [example_contact]

quarantine_log_fields = {
    'id': fields.Integer(),
    'temperature_morning': fields.Integer(required=True),
    'temperature_evening': fields.Integer(required=True),
    'log': fields.String(required=True),
    'cough': fields.Boolean(required=True),
    'head_cold': fields.Boolean(required=True),
    'fever': fields.Boolean(required=True),
    'sore_throat': fields.Boolean(required=True),
    'date': fields.DateTime(format='iso8601', required=True)
}

risk_group_fields = {
    'heart': fields.Boolean(required=True),
    'lung': fields.Boolean(required=True),
    'chronic_liver': fields.Boolean(required=True),
    'diabetis': fields.Boolean(required=True),
    'cancer': fields.Boolean(required=True),
    'weak_immunsystem': fields.Boolean(required=True),
}

contact_fields = {
    'id': fields.Integer(),
    # personal info
    'name': fields.String(required=True),
    'surname': fields.String(required=True),
    'birthdate': fields.DateTime(format='iso8601'),
    'street': fields.String(),
    'address': fields.String(),
    'zipcode': fields.Integer(),
    'email': fields.String(),
    'place': fields.String(),
    'telephone_numbers': fields.List(fields.String),
    'risk_group': fields.Nested(risk_group_fields),
    'comment_availability': fields.String(),
    'comment_language': fields.String(),
    'gender': fields.String(),
    #case information
    'exposing_case_id': fields.Integer(),
    'exposing_case_comment': fields.Integer(),
    'exposing_case_place': fields.String(),
    'status_case': fields.Integer(), #Status Falltyp
    'file_number': fields.String(), #Aktenzeichen
    'symptons_begin': fields.DateTime(format='iso8601'),
    'infectious_begin': fields.DateTime(format='iso8601'), #anfang infektionszeitraum
    'infectious_end': fields.DateTime(format='iso8601'), #ende infektionszeitraum
    'supervision_begin': fields.DateTime(format='iso8601'), #anfang beobachtungszeitrum
    'supervision_end': fields.DateTime(format='iso8601'), #ende beobachtungszeitrum
    'is_contact_person': fields.Boolean(),
    'state': fields.String(), #Bundesland
    'reporting_district': fields.String(), #meldelandkreis
    'contagious_contact_date': fields.DateTime(format='iso8601'),
    'contagious_contact_comment': fields.String(),
    'contact_person_category': fields.Integer(),
    'measures': fields.List(fields.Nested({'measure': fields.String(), 'date': fields.DateTime(format='iso8601')})),
    'sampling_type': fields.String(),
    'sampling_date': fields.DateTime(format='iso8601'),
    'sampling_result': fields.Boolean(),
    'observation_states': fields.List(fields.Nested({'state': fields.String(), 'date': fields.DateTime(format='iso8601')})),
    'comment': fields.String(),
    #monitoring
    'quarantine_monitoring_results': fields.List(fields.Nested(quarantine_log_fields)),
}

def to_json_hack(inp):
    if type(inp) is dict:
        t = {}
        for k,v in inp.items():
            t[k] = to_json_hack(v)
        return t
    if type(inp) is list:
        t = []
        for i in inp:
            t.append(to_json_hack(i))
        return t
    if isinstance(inp, datetime):
        return str(inp)
    else:
        return inp

class ContactListAPI(Resource):
    #decorators = [auth.login_required]

    def __init__(self):
        super(ContactListAPI, self).__init__()

    def get(self):
        # return {'contacts': [marshal(contact, contact_fields) for contact in contacts]}
        #return {'contacts': [json.dumps(contact, default=str) for contact in contacts]}
        return to_json_hack({'contacts': contacts})

    @use_args(contact_fields, location="json")
    def post(self, args):
        contact = dict(args)
        contact['id'] = contacts[-1]['id'] + 1 if len(contacts) > 0 else 1,
        contacts.append(contact)
        return to_json_hack({'contacts': contacts}), 201

class ContactAPI(Resource):
    #decorators = [auth.login_required]

    def __init__(self):
        super(ContactAPI, self).__init__()

    def get(self, id):
        contact = [contact for contact in contacts if contact['id'] == id]
        if len(contact) == 0:
            abort(404)
        return to_json_hack({'contact': contact[0]})

    @use_args(contact_fields, location="json")
    def put(self, id, args):
        contact = [contact for contact in contacts if contact['id'] == id]
        if len(contact) == 0:
            abort(404)
        contact = contact[0]
        for k, v in args.items():
            if v is not None:
                contact[k] = v
        return to_json_hack({'contact': contact})

    def delete(self, id):
        contact = [contact for contact in contacts if contact['id'] == id]
        if len(contact) == 0:
            abort(404)
        contacts.remove(contact[0])
        return {'result': True}

class QuarantineLogsAPI(Resource):
    #decorators = [auth.login_required]

    def __init__(self):
        super(QuarantineLogAPI, self).__init__()

    def get(self, id):
        contact = [contact for contact in contacts if contact['id'] == id]
        if len(contact) == 0:
            abort(404)
        contact = contact[0]
        if not 'quarantine_monitoring_results' in contact:
            return {'quarantine_monitoring_results': {}}
        else:
            return to_json_hack({'quarantine_monitoring_results': contact['quarantine_monitoring_results']})

    @use_args(quarantine_log_fields, location="json")
    def post(self, id, args):
        args = dict(args)
        contact = [contact for contact in contacts if contact['id'] == id]
        if len(contact) == 0:
            abort(404)
        contact = contact[0]
        if not 'quarantine_monitoring_results' in contact:
            contact['quarantine_monitoring_results'] = []
        existing = contact['quarantine_monitoring_results']
        args['id'] = existing[-1]['id'] + 1 if len(existing) > 0 else 1,
        contact['quarantine_monitoring_results'].append(args)
        return to_json_hack({'quarantine_monitoring_results': contact['quarantine_monitoring_results']}), 201

class QuarantineLogAPI(Resource):
    #decorators = [auth.login_required]

    def __init__(self):
        super(QuarantineLogAPI, self).__init__()

    def get(self, id, log_id):
        contact = [contact for contact in contacts if contact['id'] == id]
        if len(contact) == 0:
            abort(404)
        contact = contact[0]
        if not 'quarantine_monitoring_results' in contact:
            abort(404)
        log = [log for log in contacts['quarantine_monitoring_results'] if log['id'] == log_id]
        if len(log) == 0:
            abort(404)
        return to_json_hack({'quarantine_monitoring_result': log})

    @use_args(quarantine_log_fields, location="json")
    def put(self, id, log_id, args):
        args = dict(args)
        contact = [contact for contact in contacts if contact['id'] == id]
        if len(contact) == 0:
            abort(404)
        contact = contact[0]
        if not 'quarantine_monitoring_results' in contact:
            abort(404)
        log = [log for log in contacts['quarantine_monitoring_results'] if log['id'] == log_id]
        if len(log) == 0:
            abort(404)
        for k, v in args.items():
            if v is not None:
                log[k] = v
        return {'quarantine_monitoring_result': to_json_hack(log)}

    def delete(self, id, log_id):
        contact = [contact for contact in contacts if contact['id'] == id]
        if len(contact) == 0:
            abort(404)
        if not 'quarantine_monitoring_results' in contact:
            abort(404)
        log = [log for log in contacts['quarantine_monitoring_results'] if log['id'] == log_id]
        if len(log) == 0:
            abort(404)
        contacts['quarantine_monitoring_results'].remove(log[0])
        return {'result': True}

api.add_resource(ContactListAPI, '/api/v1.0/contacts', endpoint='contacts')
api.add_resource(ContactAPI, '/api/v1.0/contacts/<int:id>', endpoint='contact')
api.add_resource(QuarantineLogsAPI, '/api/v1.0/contacts/<int:id>/logs', endpoint='logs')
api.add_resource(QuarantineLogAPI, '/api/v1.0/contacts/<int:id>/logs/<int:log_id>', endpoint='log')


if __name__ == '__main__':
    app.run(debug=True)