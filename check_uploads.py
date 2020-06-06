from subprocess import check_output


def check_uploads():
    files = check_output(['mc', 'ls', 'embl/covid-if/round1']).decode('utf-8')
    files = files.split('\n')
    files = [ff.split()[-1] for ff in files if len(ff.split()) > 1]
    files = [ff for ff in files if ff.endswith('.h5')]

    uploaded_annotations = [ff for ff in files if ff.endswith('annotations.h5')]

    for upload in uploaded_annotations:
        print("Have upload", upload)
        original_file = upload.replace('_annotations.h5', '.h5')
        if original_file not in files:
            print("Could not find the associated original", original_file)

    print()
    print("Found", len(uploaded_annotations), "uploads")


if __name__ == '__main__':
    check_uploads()
