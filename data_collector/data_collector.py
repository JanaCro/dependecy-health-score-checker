import requests
from datetime import datetime, timezone, timedelta
import re
from tld import get_fld


class DataCollector:
    def __init__(self, platform_name, package_name):
        self.platform_name = platform_name
        self.package_name = package_name
        self.current_datetime = datetime.now(timezone.utc)
        self.current_datetime_3m = datetime.now(timezone.utc) - timedelta(days=90)

        # Get info from APIs
        self.project_info = requests.get(f'https://libraries.io/api/{platform_name}/{package_name}?api_key=d94e050167dc8ac6129da88e8a1e9d41').json()
        if 'error' in self.project_info:
            raise ValueError("Cannot retrieve data for specified platform/package combination!")

        self.source_rank = requests.get(f'https://libraries.io/api/{platform_name}/{package_name}/sourcerank?api_key=d94e050167dc8ac6129da88e8a1e9d41').json()
        if 'error' in self.source_rank:
            raise ValueError("Cannot retrieve data for specified platform/package combination!")

        self.contributors_info = requests.get(f'https://libraries.io/api/{platform_name}/{package_name}/contributors?api_key=d94e050167dc8ac6129da88e8a1e9d41').json()
        self.repo_info, self.repo_dependencies, self.owner, self.repository = None, None, None, None


        if 'repository_url' in self.project_info.keys() and self.project_info['repository_url'] is not None and self.project_info['repository_url'] != "" and 'github' in self.project_info['repository_url'] :
            split_values = self.project_info['repository_url'].split('/')
            self.owner, self.repository = split_values[-2], split_values[-1]

    def created_since(self):
        if 'versions' not in self.project_info.keys():
            return 0

        time_created_str = self.project_info['versions'][0]['published_at']
        time_created = datetime.strptime(time_created_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        n_months = (self.current_datetime.year - time_created.year) * 12 + self.current_datetime.month - time_created.month
        return n_months

    def updated_since(self):
        if 'latest_release_published_at' not in self.project_info.keys():
            return 0

        last_version_date = datetime.strptime(self.project_info["latest_release_published_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
        months = (self.current_datetime.year - last_version_date.year) * 12 + self.current_datetime.month - last_version_date.month
        return months

    def contributor_count(self):
        return len(self.contributors_info)

    def org_count(self):
        if type(self.contributors_info) == dict and 'error' in self.contributors_info.keys():
            return 0

        #counting distinct organisations for each package
        organizations = set()
        not_company_strs = ['retired'] # Put identifiers that do not identify a company
        for contributor in self.contributors_info:
            if 'company' not in contributor.keys() or contributor['company'] == None or contributor['company'].lower() in not_company_strs:
                # Check if company exists, if the value is None, or if the company value is in non company identifiers
                continue
            possible_companies = re.split(",", contributor['company']) # Split all of the possible companies

            # Add organizations
            for possible_company in possible_companies:
                if "former" in possible_company:
                    # Remove former organizations
                    continue
                organization = possible_company.lower() # Turn the company to lowercase
                organization = re.sub("@", "", organization) # Remove "@", because some company names start with it, for no duplicates
                organizations.add(organization)


        return len(organizations)

    #commit freqency in the last year (max 100)
    def commit_frequency(self):
        if self.owner is None or self.repository is None:
            return 0

        dates = []
        branches = self.__github_api_get(f"https://api.github.com/repos/{self.owner}/{self.repository}/branches?per_page=100") # Get a list of all branches (and their sha's)
        #ovo san dodala
        if 'message' in branches and branches['message'].lower() == 'not found':
            return 0
        shas = [branch_info['commit']['sha'] for branch_info in branches if 'main' in branch_info['name'] or 'master' in branch_info['name']]
        if shas:
            first_branch = shas[0]
        else:
            first_branch = [branch_info['commit']['sha'] for branch_info in branches][0]
        page_number = 1
        #ode su emailovi isto od commitera
        commits_per_first_branch = self.__github_api_get(f"https://api.github.com/repos/{self.owner}/{self.repository}/commits?per_page=100&sha={first_branch}&page={page_number}") # Get 100 commits of the first branch
        for commit in commits_per_first_branch:
            date = datetime.strptime(commit['commit']['committer']['date'], "%Y-%m-%dT%H:%M:%SZ") # Parse date string to datetime
            date_flag = False if (self.current_datetime.year - date.year) * 12 + (self.current_datetime.month - date.month) > 12 else True # Check if the commit was published in the last year
            if not date_flag:
                break
            dates.append(date) # Append the date of the commit to the list of dates
        return len(dates)




    def releases_count(self):
        if 'versions' not in self.project_info:
            return 0

        number_of_releases = 0
        versions = self.project_info['versions']
        for version in versions:
            number_of_releases = number_of_releases+1

        return number_of_releases

    def closed_issues_count(self):
        if self.owner is None or self.repository is None:
            return 0

        n_issues = 0
        current_datetime_3m_str = self.current_datetime_3m.strftime("%Y-%m-%dT%H:%M:%SZ")
        pg_num = 1
        issues = self.__github_api_get(f'https://api.github.com/repos/{self.owner}/{self.repository}/issues?since={current_datetime_3m_str}&state=closed&per_page=100&page={pg_num}')
        #Ovo san dodala
        if 'message' in issues and issues['message'].lower() == 'not found':
            return 0
        #100 max
        return len(issues)


    def dependencies_count(self):
        if 'dependents_count' not in self.project_info:
            return 0

        return self.project_info['dependents_count']

    def all_dependencies_updated(self):
        if 'any_outdated_dependencies' not in self.source_rank:
            return 0
        if self.source_rank['any_outdated_dependencies'] ==0:
            dep_result = 1
        else:
            dep_result = 0
        return dep_result

    def libraries_io_rank(self):
        if 'rank' not in self.project_info:
            return 0
        return self.project_info['rank']

    #checks if the package is marked as deprecated
    def deprecation(self):
        if 'is_deprecated' not in self.source_rank:
            return 0
        if self.source_rank['is_deprecated'] == 0:
            d_result = 1
        else:
            d_result = 0
        return d_result

    def maintainance(self):
        if 'is_unmaintained' not in self.source_rank:
            return 0
        if self.source_rank['is_unmaintained'] == 0:
            u_result = 1
        else:
            u_result = 0
        return u_result

    def is_removed(self):
        if 'is_removed' not in self.source_rank:
            return 0
        if self.source_rank['is_removed'] == 0:
            i_result = 1
        else:
            i_result = 0
        return i_result

    def has_recent_release(self):
        if 'recent_release' not in self.source_rank:
            return 0
        return self.source_rank['recent_release']

    #napravi da se moze isprintat text u warnings da nije accessible ali samo ako nije github
    def homepage_accessible(self):
        if 'homepage' not in self.project_info or not self.project_info['homepage']:
            return 0
        try:
            response = requests.get(self.project_info['homepage'])
            return 1 if response.status_code == 200 else 0

        except requests.exceptions.ConnectionError:
            print('connection error occurred')
            return 0

    def domain_purchase(self):
        if 'homepage' not in self.project_info or not self.project_info['homepage'] or 'github' in self.project_info['homepage']:
            return 1
        try:
            url_1 = get_fld(self.project_info['homepage'])
            URL = f'https://api.godaddy.com/v1/domains/available?domain={url_1}'
            headers_1 = {'Authorization': "sso-key gHKtnxkEd1tR_T2rvPygqPyaWXc9gGkfv5r:AKaRv9VPxv41jMAxbdMcsw"}
            domain_available = requests.get(URL, headers=headers_1)
            if domain_available.status_code == 200:
                domain = domain_available.json()
                if domain['available'] == True:
                    return 0
                else:
                    return 1
        except:
            print("error occured fetching GoDaddy data")
            return 1


    def __github_api_get(self, http):
        response = requests.get(http).json()
        if 'error' in response or (type(response) == dict and 'message' in response and response['message'].lower().startswith('api rate limit exceeded')):
            raise Exception("Rate limit for GitHub exceded. Try later in a bit.")
        return response


