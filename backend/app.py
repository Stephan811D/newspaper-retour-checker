from flask import Flask, request
from flask_restx import Api, Resource, reqparse
from flask_cors import CORS, cross_origin
import camelot
import os
import werkzeug
import pdfplumber

# Workaround für Flask-RESTx-Problem mit cached_property
werkzeug.cached_property = werkzeug.utils.cached_property

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

api = Api(app, version='1.0', title='PDF-Tabellenextraktions-API',
          description='Eine API zur Analyse von PDF-Dateien und Extraktion von Tabellen')

ns = api.namespace('tables', description='Tabellenoperationen')

# Parser für das Hochladen von PDF-Dateien
upload_parser = ns.parser()
upload_parser.add_argument('file', location='files', type=werkzeug.datastructures.FileStorage, required=True, help='PDF-Datei hochladen')

@ns.route('/upload_pdf')
@ns.expect(upload_parser)
class UploadPDF(Resource):
    @ns.doc('upload_pdf')
    @cross_origin()
    @ns.response(200, 'Erfolg')
    @ns.response(400, 'Fehlerhafte Eingabe')
    def post(self):
        '''Lade ein PDF hoch und analysiere die Tabellen'''
        args = upload_parser.parse_args()
        file = args['file']

        if file.filename == '':
            return {"error": "Keine Datei ausgewählt"}, 400

        if file and file.filename.endswith('.pdf'):
            file_path = os.path.join('uploads', file.filename)
            file.save(file_path)

            # Typ des Routenscheins herausfinden
            pfd_type = None

            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if "Remissionsschein" in text:
                        pfd_type = "Remissionsschein"
                        break  # Beende die Schleife, sobald ein Typ gefunden wurde
                    elif "Retourschein" in text:
                        pfd_type = "Retourschein"
                        print(f"Retourschein gefunden auf Seite {page.page_number}")
                        break  # Beende die Schleife, sobald ein Typ gefunden wurde

            if pfd_type is None:
                pfd_type = "Typ nicht gefunden"
                print("Kein bekannter Typ gefunden")

            print(f"Dokument ist ein {pfd_type}")

            # Camelot zur Analyse verwenden
            # Extraktion der Firmendaten-Tabelle am oberen Rand der ersten Seite
            # Passen Sie die Koordinaten des Tabellenbereichs entsprechend Ihrer PDF an
            company_tables = camelot.read_pdf(file_path, pages='1', flavor='stream', table_areas=['0,841,240,750'])

            # Extraktion der Retourschein-Informationen von der ersten Seite
            return_info_tables = camelot.read_pdf(file_path, pages='1', flavor='stream', table_areas=['310,841,595,750'])

            # Extraktion aller Content-Tabellen aus dem Dokument
            tables = camelot.read_pdf(file_path, pages='all', flavor='stream')

            if len(company_tables) == 0 and len(return_info_tables) == 0 and len(tables) == 0:
                return {"error": "Keine Tabellen gefunden"}, 400

            result = {}
            result['pdf-type'] = pfd_type

            # Verarbeitung der Firmendaten in ein Dictionary
            if len(company_tables) > 0:
                company_table = company_tables[0].df.values.tolist()
                company_dict = {}
                # Definieren Sie die Schlüssel in der Reihenfolge, in der sie in der Tabelle erscheinen
                keys = ['company-name', 'name', 'address', 'phone-number']
                for index, row in enumerate(company_table):
                    # Bereinigen Sie die Zeile, indem Sie Leerzeichen entfernen und leere Strings filtern
                    clean_row = ' '.join(item.strip() for item in row if item.strip())
                    if index < len(keys):
                        company_dict[keys[index]] = clean_row
                result['company'] = company_dict
            else:
                result['company'] = {}

            # Verarbeitung der Retourschein-Informationen
            if len(return_info_tables) > 0:
                header_table = return_info_tables[0].df.values.tolist()
                return_info_dict = {row[0]: row[1] for row in header_table if len(row) >= 2}
                result['return-information'] = return_info_dict
            else:
                result['return-information'] = {}

            # Funktion zur Erstellung eindeutiger Header
            from collections import Counter

            def make_headers_unique(headers):
                counts = Counter()
                unique_headers = []
                for header in headers:
                    counts[header] += 1
                    if counts[header] > 1:
                        unique_headers.append(f"{header}_{counts[header]}")
                    else:
                        unique_headers.append(header)
                return unique_headers

            content_list = []
            sum_dict = {}
            content_headers = None
            original_headers = None  # Speichert die ursprünglichen Header

            for idx, table in enumerate(tables):
                # Überspringen Sie die Retourschein- und Firmeninformationen, falls sie in 'tables' enthalten sind
                if (return_info_tables and table.df.equals(return_info_tables[0].df)) or (company_tables and table.df.equals(company_tables[0].df)):
                    continue

                table_data = table.df.values.tolist()

                # Für die erste Content-Tabelle: Header extrahieren
                if content_headers is None:
                    # Ignorieren Sie die ersten zwei Zeilen
                    if len(table_data) > 2:
                        table_data = table_data[2:]
                    else:
                        continue  # Überspringen, wenn nicht genug Daten vorhanden sind

                    # Verwenden Sie die nächste Zeile als Header
                    content_headers = table_data[0]
                    original_headers = content_headers.copy()  # Speichert die ursprünglichen Header
                    data_rows = table_data[1:]

                    # Stellen Sie sicher, dass die Header eindeutig sind
                    content_headers = make_headers_unique(content_headers)

                    # Umbenennen der gewünschten Header
                    header_renames = {'LM_2': 'Belastung_LM', 'RM_2': 'Gutschrift_RM'}
                    content_headers = [header_renames.get(h, h) for h in content_headers]
                else:
                    # Für nachfolgende Tabellen: Angenommen, die Header-Zeile ist nicht vorhanden
                    data_rows = table_data

                # Verarbeitung der Datenzeilen
                for row in data_rows:
                    # Überprüfen Sie, ob die Anzahl der Spalten übereinstimmt
                    if len(row) != len(content_headers):
                        continue

                    # Überprüfen, ob die Zeile eine wiederholte Header-Zeile ist
                    if all(value.strip() == header.strip() for value, header in zip(row, original_headers)):
                        continue  # Überspringen Sie die Zeile, wenn alle Werte den ursprünglichen Headern entsprechen

                    row_dict = dict(zip(content_headers, row))

                    # Überprüfen, ob es sich um die Summenzeile handelt
                    if (not row_dict.get('Titel') and not row_dict.get('Objektnr') and not row_dict.get('Folge')):
                        # Entfernen der unerwünschten Felder aus sum_dict
                        keys_to_remove = ['Titel', 'Objektnr', 'Folge', '', 'MWST.', 'EK.Pr.', 'VK.Pr.', 'Belastung_LM']
                        for key in keys_to_remove:
                            row_dict.pop(key, None)
                        sum_dict = row_dict
                    else:
                        content_list.append(row_dict)

            # Finale Ergebnisse
            result['content'] = content_list
            result['sum'] = sum_dict

            # Datei bleibt auf dem Server erhalten, wird nicht gelöscht

            return result, 200  # Rückgabe ohne 'tables'-Schlüssel
        else:
            return {"error": "Ungültiges Dateiformat"}, 400

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
