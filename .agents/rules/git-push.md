# Git Push Policy

- **NGHIÊM CẤM TỰ ĐỘNG PUSH CODE**: Tuyệt đối KHÔNG được phép tự động chạy lệnh `git push` hoặc đẩy code lên remote repository.
- **ĐIỀU KIỆN ĐƯỢC PHÉP PUSH**: Chỉ thực hiện lệnh `git push` khi và chỉ khi người dùng nhập lệnh rõ ràng là `"git push"`.
- Tất cả các thao tác chỉnh sửa, kiểm tra, debug, hoặc commit đều phải giữ ở môi trường local cho đến khi có lệnh `"git push"` từ người dùng.
