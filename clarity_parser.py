import clarify
import requests
import zipfile, StringIO
import unicodecsv

def statewide_results(url):
    j = clarify.Jurisdiction(url=url, level="state")
    r = requests.get(j.report_url('xml'), stream=True)
    z = zipfile.ZipFile(StringIO.StringIO(r.content))
    z.extractall()
    p = clarify.Parser()
    p.parse("detail.xml")
    results = []
    for result in p.results:
        candidate = result.choice.text
        office, district = parse_office(result.contest.text)
        party = parse_party(result.contest.text)
        if party is None and '(' in candidate:
            candidate, party = candidate.split('(')
            candidate = candidate.strip()
            party = party.replace(')','').strip()
        if result.jurisdiction:
            county = result.jurisdiction.name
        else:
            county = None
        r = [x for x in results if x['county'] == county and x['office'] == office and x['district'] == district and x['party'] == party and x['candidate'] == candidate]
        if r:
             r[0][result.vote_type] = result.votes
        else:
            results.append({ 'county': county, 'office': office, 'district': district, 'party': party, 'candidate': candidate, result.vote_type: result.votes})

    with open("20121204__ga__general__runoff.csv", "wb") as csvfile:
        w = unicodecsv.writer(csvfile, encoding='utf-8')
        w.writerow(['county', 'office', 'district', 'party', 'candidate', 'votes', 'election_day', 'absentee', 'early_voting', 'provisional'])
        for row in results:
            total_votes = row['Election Day'] + row['Absentee by Mail'] + row['Advance in Person'] + row['Provisional']
            w.writerow([row['county'], row['office'], row['district'], row['party'], row['candidate'], total_votes, row['Election Day'], row['Absentee by Mail'], row['Advance in Person'], row['Provisional']])

def download_county_files(url, filename):
    no_xml = []
    j = clarify.Jurisdiction(url=url, level="state")
    subs = j.get_subjurisdictions()
    for sub in subs:
        try:
            r = requests.get(sub.report_url('xml'), stream=True)
            z = zipfile.ZipFile(StringIO.StringIO(r.content))
            z.extractall()
            precinct_results(sub.name.replace(' ','_').lower(),filename)
        except:
            no_xml.append(sub.name)

    print no_xml

def precinct_results(county_name, filename):
    f = filename + '__' + county_name + '__precinct.csv'
    p = clarify.Parser()
    p.parse("detail.xml")
    results = []
    vote_types = []
    for result in [x for x in p.results if not 'Number of Precincts' in x.vote_type]:
        vote_types.append(result.vote_type)
        candidate = result.choice.text
        office, district = parse_office(result.contest.text)
        party = parse_party(result.contest.text)
        if '(' in candidate and party is None:
            if '(I)' in candidate:
                candidate, party = candidate.split('(I)')
                candidate = candidate.strip() + ' (I)'
            else:
                candidate, party = candidate.split('(')
                candidate = candidate.strip()
            party = party.replace(')','').strip()
        county = p.region
        if result.jurisdiction:
            precinct = result.jurisdiction.name
        else:
            precinct = None
        r = [x for x in results if x['county'] == county and x['precinct'] == precinct and x['office'] == office and x['district'] == district and x['party'] == party and x['candidate'] == candidate]
        if r:
             r[0][result.vote_type] = result.votes
        else:
            results.append({ 'county': county, 'precinct': precinct, 'office': office, 'district': district, 'party': party, 'candidate': candidate, result.vote_type: result.votes})

    vote_types = list(set(vote_types))
    with open(f, "wb") as csvfile:
        w = unicodecsv.writer(csvfile, encoding='utf-8')
        headers = ['county', 'precinct', 'office', 'district', 'party', 'candidate', 'votes'] + [x.replace(' ','_').lower() for x in vote_types]
        w.writerow(headers)
        for row in results:
            if 'Republican' in row['office']:
                row['party'] = 'REP'
            elif 'Democrat' in row['office']:
                row['party'] = 'DEM'
            total_votes = sum([row[k] for k in vote_types])
            w.writerow([row['county'], row['precinct'], row['office'], row['district'], row['party'], row['candidate'], total_votes] + [row[k] for k in vote_types])


def parse_office(office_text):
    if ' - ' in office_text:
        office = office_text.split('-')[0]
    else:
        office = office_text.split(',')[0]
    if ', District' in office_text:
        district = office_text.split(', District')[1].split(' - ')[0].strip()
    elif 'United States Senator' in office_text:
        office = 'United States Senator'
        district = None
    elif ',' in office_text:
        district = office_text.split(',')[1]
    else:
        district = None
    return [office.strip(), district]

def parse_party(office_text):
    if '- REP' in office_text:
        party = 'REP'
    elif '- DEM' in office_text:
        party = 'DEM'
    else:
        party = None
    return party
