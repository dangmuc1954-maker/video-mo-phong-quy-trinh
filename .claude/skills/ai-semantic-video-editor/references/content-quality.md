# Nội dung có ý nghĩa — không tạo cho có lệ

**Mọi yếu tố trong video (kịch bản, lời thoại, cảnh, nhân vật, mốc thời gian, graphic, phụ đề, chuyển cảnh, nhạc) đều phải có lý do tồn tại, phục vụ một thông điệp chung và nhất quán với nhau.** Phép thử: bỏ yếu tố đó đi mà video không mất gì thì nó là thừa, phải cắt hoặc làm lại.

## 1. Kịch bản: một thông điệp, một mạch
- Trước khi viết, chốt **1 câu thông điệp** (người xem nhớ gì sau video) và **1 câu logline** (mạch chuyện từ đầu tới cuối). Mọi thứ phía sau đều phải phục vụ hai câu này.
- Cấu trúc có diễn biến: hook nêu vấn đề hoặc tò mò → triển khai → leo thang hoặc bước ngoặt → kết hoặc bài học hoặc CTA. Không xếp các ý rời rạc cạnh nhau.
- Mỗi câu chở **thông tin mới hoặc cảm xúc mới**, không lặp ý.
- Cấm câu sáo rỗng: "thật tuyệt vời", "vô cùng ý nghĩa", "hãy cùng xem nhé", "bạn sẽ bất ngờ". Thay bằng chi tiết cụ thể: con số, hình ảnh, hành động, hệ quả.
- Review / thông tin: mọi khẳng định phải có căn cứ (số liệu kèm nguồn, trải nghiệm cụ thể). Đạo lý: phải có ví dụ hoặc ẩn dụ chứng minh, không chỉ hô khẩu hiệu.

## 2. Lời thoại
- **Giọng kể thú vị, vui nhộn (khen người xem, mồi vấn đề, đặt tên, ví von, câu chốt): đọc `giong-ke-hay.md` trước khi viết lời kể.**
- Đúng giọng của người nói (người kể trầm tĩnh, KOC hào hứng, nhân vật theo tính cách đã chốt) và **giữ giọng đó suốt video**.
- Câu ngắn, có nhịp; ngắt nghỉ đặt ở chỗ cần nhấn.
- Câu chốt cuối phải đọng lại thông điệp, không phải một câu kết chung chung.

## 3. Cảnh
- Mỗi cảnh trả lời được: **cảnh này cho người xem THẤY điều gì mà lời nói đang nói?** Không trả lời được thì viết lại.
- Cảnh sau là hệ quả hoặc bước tiếp theo của cảnh trước: nhân quả, thời gian, không gian liền mạch. Không chèn cảnh đẹp chung chung để lấp chỗ.
- Hành động phải mang nghĩa: vứt cuốc là bỏ cuộc, sương tan là sự thật lộ ra, kem tan là thấm nhanh.

## 4. Nhân vật
- Mỗi nhân vật có **vai trò trong thông điệp** (người bỏ cuộc / người kiên trì, người dùng sản phẩm) và **ngoại hình cố định** trong `subjects`: tuổi, trang phục, đặc điểm. Ngoại hình chỉ đổi khi câu chuyện yêu cầu (ví dụ "10 năm sau"), và phải ghi rõ trong prompt.
- Không thêm nhân vật không có vai.

## 5. Mốc thời gian
- Cắt cảnh **ở ranh giới câu hoặc ý**, không cắt giữa câu.
- Graphic bật lên **đúng từ khóa** (trước 0.1s), giữ đủ để đọc, tắt khi ý đó kết thúc.
- Phụ đề khớp lời đọc từng cụm. Khoảnh khắc chính của cảnh rơi đúng lúc câu đó được đọc.
- Nhịp theo cảm xúc: chậm ở đoạn suy ngẫm, nhanh ở đoạn cao trào hoặc liệt kê.

## 6. Graphic, phụ đề, chuyển cảnh, nhạc
- **Graphic**: mỗi cái phải làm rõ hoặc nhấn một ý cụ thể vừa được nói (số liệu, so sánh, bài học). Không có ý thì không chèn. Cùng một bảng màu và font suốt video.
- **Phụ đề**: đúng chữ lời đọc, đủ dấu; từ khóa được nhấn phải là từ quan trọng nhất của câu.
- **Chuyển cảnh**: cảnh liền mạch thì cắt thẳng; đổi không gian hoặc thời gian thì hòa tan nhẹ. Không dùng hiệu ứng chuyển cảnh chỉ để cho có.
- **Nhạc nền**: hợp cảm xúc chủ đạo, nhỏ dưới giọng đọc; đổi nhạc chỉ khi đổi cảm xúc.

## 7. Bảng tự kiểm (BẮT BUỘC, ghi kết quả vào bảng duyệt kịch bản)

| Hỏi | Đạt khi |
|---|---|
| Thông điệp 1 câu là gì? | Viết ra được, và câu chốt của video nói đúng nó |
| Mỗi cảnh có cho THẤY đúng câu thoại của nó không? | Có, với từng cảnh |
| Có câu thoại sáo rỗng hoặc lặp ý không? | Không còn câu nào |
| Có cảnh, graphic hay hiệu ứng nào bỏ đi mà không mất gì không? | Không còn |
| Nhân vật, bối cảnh, phong cách có giữ nguyên qua mọi cảnh không? | Có (`subjects`, `style` cố định, `continue_from_previous` hợp lý) |
| Số liệu và khẳng định có nguồn không? | Có, hoặc ghi rõ "minh họa giả định" |
| Cảnh có cắt ở ranh giới câu, graphic có bật đúng từ khóa không? | Có (kiểm bằng `sync.json`) |

Không đạt mục nào thì sửa trước khi tạo cảnh hoặc lồng tiếng (tạo cảnh và tạo giọng đều tốn lượt). Sau khi xuất video, kiểm lại bằng khung hình thật trước khi gửi anh.
