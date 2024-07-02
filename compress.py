import os
import zipfile


def compress_directory(
    directory_path: str,
    output_name: str,
    on_compress=lambda x, y: None,
    compress_done=lambda x, y: None,
):
    with zipfile.ZipFile(output_name, "w", zipfile.ZIP_DEFLATED) as zip:
        for path, _, filenames in os.walk(directory_path):
            for filename in filenames:
                local_filepath = os.path.join(path, filename)
                zip_filepath = local_filepath[len(directory_path) + 1 :]
                on_compress(local_filepath, zip_filepath)
                zip.write(local_filepath, zip_filepath)
                compress_done(local_filepath, zip_filepath)


def compress_file(
    filepath: str,
    output_name: str,
    on_compress=lambda x, y: None,
    compress_done=lambda x, y: None,
):
    with zipfile.ZipFile(output_name, "w", zipfile.ZIP_DEFLATED) as zip:
        zip_filepath = os.path.basename(filepath)
        on_compress(filepath, zip_filepath)
        zip.write(filepath, zip_filepath)
        compress_done(filepath, zip_filepath)


def decompress(zip_filepath: str, target_directory_path: str):
    with zipfile.ZipFile(zip_filepath, "r") as zip:
        zip.extractall(target_directory_path)


if __name__ == "__main__":
    compress_directory(
        "../network-playground",
        "test.zip",
        lambda x, y: print(x + " ->", y),
        lambda x, y: print(x + " ->", y),
    )

    compress_file("run.bat", "run.bat.zip")
    # lambda x: None()
