import re
from collections import OrderedDict

class S3Manager:

    def __init__(self, s3_client, bucket_name):
        self.s3_client    = s3_client
        self.bucket_name  = bucket_name

    def list_files(self, year=None):
        files_by_year = OrderedDict()

        # List all files in the bucket
        response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)

        if 'Contents' in response:
            for obj in response['Contents']:

                file_key = obj['Key']

                # Try to find a year in the file name
                result = re.search(r'\d{4}', file_key)

                if result:
                    file_year = result.group(0)

                    if year and file_year != year:
                        continue

                    if file_year not in files_by_year:
                        files_by_year[file_year] = []

                    # Add to the dictionary with the year as the key and the path as the value
                    files_by_year[file_year].append(file_key)

        files_by_year = OrderedDict(sorted(files_by_year.items(), key=lambda x: x[0]))

        return files_by_year
    
    def get_file_id(self,  file_key):
        response = self.s3_client.list_object_versions(Bucket=self.bucket_name, Prefix=file_key)
        version_id = ''
        for version in response.get('DeleteMarkers', []):
            if version.get('IsLatest'):
                version_id = version.get('VersionId')
                break

        return version_id

    def download_file(self, file_key, local_file_path):
        try:
            self.s3_client.download_file(self.bucket_name, file_key, local_file_path)
            return True, "Download realizado com sucesso."
        except Exception as e:
            return False, f"{str(e)}"

    def delete_file(self, file_key, file_id=None):
        try:
            if not file_id:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            else:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key, VersionId=file_id)
            return True, "Download realizado com sucesso."
        except Exception as e:
            return False, f"{str(e)}"
