import unittest
from data_collector import DataCollector


#sslext:sslext - outdated dep
#oauth2client - marked as deprecated
#aopalliance:aopalliance - 0 previous versions, 0 maintainers
#lodash - popular npm package that seems unmaintained
#axios, cloudinary - very good npm packages
#owoifyx - bad npm package
#npm - whne there is a scope / will throw an error, use %2F instead
#flask-oidc za hostile takeover uskoro istice
#pix-diff low npmpackage
#contributori su mu krivi nekad

class DataCollectorTester(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(DataCollectorTester, self).__init__(*args, **kwargs)
        self.data_loader = DataCollector('pypi', 'urllib3')

    def test_created_since(self):
        date = self.data_loader.created_since()
        print("Created since: ", date)
        self.assertIsNotNone(date)

    def test_updated_since(self):
        months = self.data_loader.updated_since()
        print("Updated since (months): ", months)
        self.assertIsNotNone(months)

    def test_contributor_count(self):
        n_contributors = self.data_loader.contributor_count()
        print("Contributor number: ", n_contributors)
        self.assertIsNotNone(n_contributors)

    def test_org_count(self):
        n_orgs = self.data_loader.org_count()
        print("Number of (distincit) organizations: ", n_orgs)
        self.assertIsNotNone(n_orgs)

    def test_commit_frequency(self):
        commit_freq = self.data_loader.commit_frequency()
        print("Commit frequency: ", commit_freq)
        self.assertIsNotNone(commit_freq)

    def test_recent_releases_count(self):
        n_releases = self.data_loader.releases_count()
        print("Number of releases: ", n_releases)
        self.assertIsNotNone(n_releases)

    def test_closed_issues_count(self):
        n_closed_issues = self.data_loader.closed_issues_count()
        print("Closed issues: ", n_closed_issues)
        self.assertIsNotNone(n_closed_issues)

    def test_dependencies_count(self):
        n_deps = self.data_loader.dependencies_count()
        print("Num of dependants: ", n_deps)
        self.assertIsNotNone(n_deps)

    def test_outdated_dependencies(self):
        n_outdated = self.data_loader.all_dependencies_updated()
        print("All dependencies updated", n_outdated)
        self.assertIsNotNone(n_outdated)

    def test_libraries_rank(self):
        n_rank = self.data_loader.libraries_io_rank()
        print("Libraries.io rank is", n_rank)
        self.assertIsNotNone(n_rank)

    def test_is_deprecated(self):
        n_not_deprecated = self.data_loader.deprecation()
        print("The package is not abandoned", n_not_deprecated)
        self.assertIsNotNone(n_not_deprecated)

    def test_is_unmaintained(self):
        n_maintained = self.data_loader.maintainance()
        print("The package is maintained", n_maintained)
        self.assertIsNotNone(n_maintained)

    def test_is_removed(self):
        n_removed = self.data_loader.is_removed()
        print("The package is present", n_removed)
        self.assertIsNotNone(n_removed)

    def test_recent_release(self):
        n_release = self.data_loader.has_recent_release()
        print("The package has a recent release", n_release)
        self.assertIsNotNone(n_release)

    def test_homepage(self):
        n_acessible = self.data_loader.homepage_accessible()
        print("Homepage accessibility", n_acessible)
        self.assertIsNotNone(n_acessible)

