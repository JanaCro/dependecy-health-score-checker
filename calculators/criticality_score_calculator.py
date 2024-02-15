import numpy as np
import requests
import whois
from datetime import datetime


from data_collector import DataCollector
from typing import Union, Tuple


class CriticalityScoreCalculator:
    def __init__(self, keys_ordered: list, thresh_num: Union[np.ndarray, list], thresh_den: Union[np.ndarray, list]):
        self.keys_ordered = keys_ordered
        self.thresh_num = thresh_num if isinstance(thresh_num, np.ndarray) else np.array(thresh_num)
        self.thresh_den = thresh_den if isinstance(thresh_den, np.ndarray) else np.array(thresh_den)
        self.update = lambda: None
        self.parameters = None

    def calculate_criticality_score(self, package_name: str, platform_name: str, weights: Union[np.ndarray, list]) -> Tuple[float, str]:
        weights = np.array(weights) if not isinstance(weights, np.ndarray) else weights
        parameters_np = self.get_parameters(package_name, platform_name)

        x = np.log(1 + np.maximum(parameters_np, self.thresh_num)) / np.log(1 + np.maximum(parameters_np, self.thresh_den))
        y = (x @ weights) / np.sum(np.abs(weights))
        score = round(y, 3)

        text = self.format_info_text(score, self.parameters, package_name, platform_name)

        return score, text

    def get_parameters(self, package_name: str, platform_name: str) -> np.ndarray:
        self.parameters = {k:'' for k in self.keys_ordered}

        # Set the data collector
        data_loader = DataCollector(platform_name, package_name)

        # Get the parameters of this package
        self.parameters['created_since'] = data_loader.created_since()
        self.update()

        self.parameters['updated_since'] = data_loader.updated_since()
        self.update()

        self.parameters['contributor_count'] = data_loader.contributor_count()
        self.update()

        self.parameters['org_count'] = data_loader.org_count()
        self.update()

        self.parameters['commit_frequency'] = data_loader.commit_frequency()
        self.update()

        self.parameters['releases_count'] = data_loader.releases_count()
        self.update()

        self.parameters['closed_issues_count'] = data_loader.closed_issues_count()
        self.update()

        self.parameters['dependant_projects_count'] = data_loader.dependencies_count()
        self.update()

        self.parameters['all_dependencies_updated']  = data_loader.all_dependencies_updated()
        self.update()

        self.parameters['lib_rank'] = data_loader.libraries_io_rank()
        self.update()

        self.parameters['not_deprecated'] = data_loader.deprecation()
        self.update()

        self.parameters['maintained'] = data_loader.maintainance()
        self.update()

        self.parameters['not_removed'] = data_loader.is_removed()
        self.update()

        self.parameters['recent_release'] = data_loader.has_recent_release()
        self.update()

        self.parameters['homepage_accessible'] = data_loader.homepage_accessible()
        self.update()



        return np.array(list(self.parameters.values()))

    def set_update_pb(self, update_progressbar): #to communicate with update_progressbar from main GUI
        self.update = update_progressbar

    def format_info_text(self, score, parameters, package_name, platform_name):
        text = ''
        if score <= 0.50:
            text += 'Very low score (under 50%), indicates that the package is unmaintained or abandoned\n'
        if score > 0.50 and score < 0.60:
            text+= 'Low score (50%-60%), the package could be insufficiently maintained\n'
        if parameters['not_deprecated'] == 0:
            text += 'WARNING! - This package is marked as deprecated \n'
        if parameters['all_dependencies_updated'] == 0:
            text += 'WARNING! - This package has outdated dependencies, it might be deprecated \n'
        if parameters['contributor_count'] == 0:
            text += 'WARNING! - This package does not have any contributors, it might be insufficiently maintained \n'
        if parameters['releases_count'] == 1:
            text += 'WARNING! - This package has 0 previous versions, could be malicious \n'
        if parameters['homepage_accessible'] == 0:
            text += 'WARNING! - Homepage is either not provided, does not exist, or is not reachable! Indicates deprecation! \n'
        if parameters['maintained'] == 0:
            text += 'WARNING! - This package is marked as unmaintained \n'
        if parameters['not_removed'] == 0:
            text += 'WARNING! - This package is removed from the package manager, indicates deprecation \n'
        if parameters['updated_since'] > 24:
            t = parameters['updated_since']/12
            text += f"WARNING! - This package has not been updated for {round(t,2)} years, indicates deprecation \n"
        elif parameters['updated_since'] > 10 and parameters['commit_frequency'] < 10 and parameters['closed_issues_count'] < 5:
            text += f"WARNING! - This package has not been updated for {parameters['updated_since']} months, has {parameters['commit_frequency']} commits in the last year and {parameters['closed_issues_count']} closed issues in the last 3 months, might be insufficiently maintained."
        elif parameters['updated_since'] > 10 and parameters['commit_frequency'] < 10:
            text += f"WARNING! - This package has not been updated for {parameters['updated_since']} months and has {parameters['commit_frequency']} commits in the last year, might be insufficiently maintained."
        elif parameters['updated_since'] > 10 and parameters['closed_issues_count'] < 5:
            text += f"WARNING! - This package has not been updated for {parameters['updated_since']} months and has {parameters['closed_issues_count']} closed issues in the last 3 months, might be insufficiently maintained"

        if parameters['created_since'] < 4:
            text += f'WARNING! - This package is only {parameters["created_since"]} months old, could be malicious!'

        text += self.hostile_takeover_msg(package_name, platform_name)

        if text == '':
            text += 'No warnings found, seems good :).\n Check the score.'
        return text

    def hostile_takeover_msg(self, package_name, platform_name):
        domains = []
        blacklist_domains = ['gmail', 'yahoo', 'hotmail']
        text = ''
        if platform_name == 'npm':
            npm_info = requests.get(f'https://registry.npmjs.org/{package_name}').json()
            maintainers = npm_info['maintainers'] if 'maintainers' in npm_info else []
            maintainers = [maintainers] if not isinstance(maintainers, list) else maintainers
            authors = npm_info['author'] if 'author' in npm_info else []
            authors = [authors] if not isinstance(authors, list) else authors
            domains += [info['email'].split('@')[1] for info in maintainers + authors if 'email' in info]
        elif platform_name == 'pypi':
            pypi_info = requests.get(f'https://pypi.org/pypi/{package_name}/json').json()
            if 'info' in pypi_info and 'author_email' in pypi_info['info'] and pypi_info['info']['author_email'] != '':
                domains += [mail.strip(' <>').split('@')[1] for mail in
                            pypi_info['info']['author_email'].split(',')]  # Autori su odvojeni zarezom

        domains = [d for d in domains if d.split('.')[0] not in blacklist_domains]
        for domain in domains:
            try:
                print(f'the domain name is {domain} ')
                info = whois.whois(domain)
                if 'expiration_date' in info:
                    if isinstance(info['expiration_date'], list):
                        expiration_date = info['expiration_date'][0]
                    else:
                        expiration_date = info['expiration_date']

                    if expiration_date in ['null', None, '']:
                        text += f'Domain {domain} expiration date not specified, could indicate domain is available for purchase. Check the status below or purchasibility. Possible hostile takeover attack!\n'

                    elif datetime.now() > expiration_date:
                        text += f"The domain {domain} has expired, this package is potentially vulnerable to hostile takeover attack through domain hijack! Check domain status! \n"

                    elif (expiration_date - datetime.now()).days < 60:
                        ex_days = (expiration_date - datetime.now()).days
                        text += f"The domain {domain} will expire in {ex_days} days, regularly check if it is updated, if not, the package is vulnerable to hostile takeover attack. \n"

                if 'status' in info and info['status'] != None and info['status'] != 'null' and info['status'] != '':
                    info_status = info['status'] if isinstance(info['status'], list) else [info['status']]
                    statuses = [s.split(' ')[0] for s in info_status]  # There can be more than one
                    for status in statuses:
                        print(status)
                        if status.lower() == 'inactive':
                            text += f'The domain {domain} has {status} status, it is not activated. Check for purchasibility, possible hostile takeover attack!\n'
                        elif status.lower() == 'ok' or status.lower() == 'active':
                            text += f'The domain {domain} has {status} status, which could indicate it is available for purchase, no restrictions. Check for purchasibility, possible hostile takeover attack!\n '
                        elif status.lower() == 'pendingdelete' or status.lower() == 'pending delete':
                            text += f'The domain {domain} has {status} status, it will soon be purged and available for purchase. Hostile takeover attack possible!\n'
                        elif status.lower() == 'pendingrestore' or status.lower() == 'pending restore':
                            text += f'The domain {domain} has {status} status, it will be available for purchase if documentation is not provided on time. Check for purchasibility, possible hostile takeover! \n'
                        elif status.lower() == 'redemptionperiod' or status.lower() == 'redemption period':
                            text += f'The domain {domain} has {status} status for 30 days after which it is available for purchase. Hostile takeover attack possible! \n'
                        elif 'lock' in status.lower() or 'expired' in status.lower():
                            text += f'The domain {domain} has {status} status, check for purchasibility, possible hostile takeover attack!\n'


            except whois.parser.PywhoisError as e:
                text += 'The domain has no match, it is not registered and is available for purchase. This package is vulnerable to hostile takeover attack.'

        return text
