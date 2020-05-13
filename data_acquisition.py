import requests
import boto3
from botocore.exceptions import NoCredentialsError


def downloadFile(link, filename):
    mid_file = requests.get(link, stream=True)
    with open(filename, 'wb') as saveMidFile:
        saveMidFile.write(mid_file.content)
        print('Downloaded {} successfully.'.format(filename))


def upload_to_aws(local_file, bucket, s3_file):
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_KEY)

    try:
        s3.upload_file(local_file, bucket, s3_file)
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False


ACCESS_KEY = ''
SECRET_KEY = ''

# Michael_Jackson_Billie_Jean
filename_Michael_Jackson_Billie_Jean = "Michael_Jackson_Billie_Jean.mid"
downloadFile('https://bitmidi.com/uploads/73866.mid',
             filename_Michael_Jackson_Billie_Jean)
uploaded_Michael_Jackson_Billie_Jean = \
    upload_to_aws(filename_Michael_Jackson_Billie_Jean,
                  'midi-samples', filename_Michael_Jackson_Billie_Jean)

# A_Whole_New_World
filename_A_Whole_New_World = "A_Whole_New_World.mid"
downloadFile('https://bitmidi.com/uploads/3186.mid',
             filename_A_Whole_New_World)
uploaded_A_Whole_New_World = upload_to_aws(filename_A_Whole_New_World,
                                           'midi-samples',
                                           filename_A_Whole_New_World)

# ACDC_Thunderstruck_K
filename_ACDC_Thunderstruck_K = "ACDC_Thunderstruck_K.mid"
downloadFile('https://bitmidi.com/uploads/3654.mid',
             filename_ACDC_Thunderstruck_K)
uploaded_ACDC_Thunderstruck_K = upload_to_aws(filename_ACDC_Thunderstruck_K,
                                              'midi-samples',
                                              filename_ACDC_Thunderstruck_K)

# Pirates_of_the_Caribbean
filename_Pirates_of_the_Caribbean = "Pirates_of_the_Caribbean.mid"
downloadFile('https://bitmidi.com/uploads/85261.mid',
             filename_Pirates_of_the_Caribbean)
uploaded_Pirates_of_the_Caribbean = \
    upload_to_aws(filename_Pirates_of_the_Caribbean, 'midi-samples',
                  filename_Pirates_of_the_Caribbean)

# Star_Wars_Theme
filename_Star_Wars_Theme = "Star_Wars_Theme.mid"
downloadFile('https://bitmidi.com/uploads/96653.mid', filename_Star_Wars_Theme)
uploaded_Star_Wars_Theme = upload_to_aws(filename_Star_Wars_Theme,
                                         'midi-samples',
                                         filename_Star_Wars_Theme)
