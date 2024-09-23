class Text:
    def __init__(
        self,
        ip_label: str,
        ip_edit_button: str,
        filepath_title_label: str,
        select_file_button: str,
        select_directory_button: str,
        sync_button: str,
        close_button: str,
        dialog_select_file: str,
        dialog_select_directorty: str,
        ip_edit_dialog_title: str,
        ip_edit_dialog_label: str,
        compressing: str,
        compress_done: str,
        sending_file_to_remote: str,
        send_success: str,
        pulling_from_remote: str,
        pull_success: str,
        sync_success: str,
        syncing: str,
        err_mismatch_file_name: str,
        same_hash_skip: str,
        uploading_file: str,
        upload_file_success: str,
        downloading_file: str,
        download_file_success: str,
        decompressing: str,
        decompress_success: str,
        fail: str,
        unable_to_start_grpc_server: str,
        title: str,
        receiving_file: str,
        receive_file_successful: str,
        sending_file: str,
        syncing_file_to: str,
    ) -> None:
        self.ip_label = ip_label
        self.ip_edit_button = ip_edit_button
        self.filepath_title_label = filepath_title_label
        self.select_file_button = select_file_button
        self.select_directory_button = select_directory_button
        self.sync_button = sync_button
        self.close_button = close_button
        self.dialog_select_file = dialog_select_file
        self.dialog_select_directorty = dialog_select_directorty
        self.ip_edit_dialog_title = ip_edit_dialog_title
        self.ip_edit_dialog_label = ip_edit_dialog_label
        self.compressing = compressing
        self.compress_done = compress_done
        self.sending_file_to_remote = sending_file_to_remote
        self.send_success = send_success
        self.pulling_from_remote = pulling_from_remote
        self.pull_success = pull_success
        self.sync_success = sync_success
        self.syncing = syncing
        self.err_mismatch_file_name = err_mismatch_file_name
        self.same_hash_skip = same_hash_skip
        self.uploading_file = uploading_file
        self.upload_file_success = upload_file_success
        self.downloading_file = downloading_file
        self.download_file_success = download_file_success
        self.decompressing = decompressing
        self.decompress_success = decompress_success
        self.fail = fail
        self.unable_to_start_grpc_server = unable_to_start_grpc_server
        self.title = title
        self.receiving_file = receiving_file
        self.receive_file_successful = receive_file_successful
        self.sending_file = sending_file
        self.syncing_file_to = syncing_file_to


cn = Text(
    "远程地址:",
    "修改",
    "目标:",
    "选择文件",
    "选择文件夹",
    "同步",
    "关闭",
    "选择文件",
    "选择文件夹",
    "修改地址",
    "请输入地址",
    "正在压缩",
    "压缩完成",
    "正在发送文件到远端",
    "发送成功",
    "正在从远端拉取文件",
    "拉取成功",
    "同步成功",
    "开始同步",
    "错误：文件名不一致",
    "文件一致，跳过",
    "正在上传文件",
    "上传文件成功",
    "正在下载文件",
    "下载文件成功",
    "正在解压",
    "解压成功",
    "失败",
    "无法启动grpc服务器",
    "游戏存档同步工具",
    "正在接收文件",
    "接收文件成功",
    "正在发送文件",
    "同步文件到{}中"
)

en = Text(
    "remote ip:",
    "edit",
    "target:",
    "Select File",
    "Select Directory",
    "Sync",
    "Close",
    "Select File",
    "Select Directory",
    "Edit Remote IP",
    "Please Input Remote IP",
    "compressing",
    "compress done",
    "sending file to remote",
    "send successful",
    "pulling data from remote",
    "pull successful",
    "sync successful",
    "syncing",
    "error: mismatch file name",
    "file is already synced,skip",
    "uploading file",
    "upload file success",
    "downloading file",
    "download file successful",
    "decompressing",
    "decompress successful",
    "fail",
    "unable to start grpc server",
    "Game Save Sync",
    "receiving file",
    "receive file successful",
    "sending file",
    "syncing file to {}"
)


def get_i18n_text(code: str):
    if code == "cn":
        return cn
    return en
