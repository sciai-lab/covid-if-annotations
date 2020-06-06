from subprocess import check_outputs


def check_uploads():
    files = check_outputs(['mc', 'ls', 'embl/covid-if/round1'])
    print(files)
    files = files.split('\n')
    files = [ff for ff in files if ff.endswith('.h5')]

    uploaded_annotations = [ff for ff in files if ff.endswith('annotations.h5')]

    for upload in uploaded_annotations:
        print("Have upload", upload)
        original_file = upload.replace('annotations.h5', 'h5')
        if original_file not in files:
            print("Could not find the associated original", original_file)


if __name__ == '__main__':
    check_uploads()
