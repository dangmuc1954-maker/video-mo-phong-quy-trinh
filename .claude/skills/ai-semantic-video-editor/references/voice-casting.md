# Chọn giọng ElevenLabs cho video (voice casting)

## Thứ tự ưu tiên
1. **Anh gửi voice ID** → dùng đúng ID đó, không đổi.
2. **Anh nói "giọng cũ" / "giọng lần trước"** → để trống `voice_id`; dòng TTS mới kế thừa giọng của dòng trước.
3. **Anh không đưa ID** → em TỰ CHỌN giọng hợp video theo quy trình dưới đây, ghi rõ giọng đã chọn và lý do trong bảng duyệt kịch bản. Anh muốn đổi thì gửi ID khác.

## Quy trình tự chọn
1. Đọc kịch bản và xác định: ngôn ngữ, ai đang kể (người kể chuyện, nhân vật, người review), đối tượng người xem, cảm xúc chủ đạo, nhịp.
2. Đặt bộ lọc theo bảng gợi ý rồi tìm:
   `python scripts/voice_catalog.py search --language vi --gender male --age middle_aged --use-case narrative_story --keywords "deep warm calm" --top 15`
   Không ra kết quả thì nới dần bộ lọc: bỏ `--age`, rồi `--use-case`, rồi `--accent`.
3. Chọn 1 giọng chính và 2 giọng dự phòng. Tiêu chí, xếp theo thứ tự quan trọng:
   - `language` đúng ngôn ngữ kịch bản. Video tiếng Việt thì chọn giọng `vi`: giọng nước ngoài đọc tiếng Việt thường lơ lớ, sai dấu.
   - Hợp vai: giới tính, tuổi, vùng miền, tính cách.
   - Đã được kiểm chứng: `source: tool` (đã dùng thật trong tool), `premade`, hoặc `cloned_by_count` cao.
   - `free_users_allowed` khác `false`.
4. Ghi vào storyboard:
   ```json
   "narration_voice": {"voice_id": "…", "name": "…", "auto": true,
                       "reason": "nam trung niên, trầm ấm, giọng Bắc, hợp đạo lý", "backup": ["…", "…"]}
   ```
5. `tts_macro.py` dán `voice_id` vào ô **Voice ID** của tool → **Tải giọng** → tạo.
6. Nghe lại kết quả. Giọng lơ lớ, sai dấu hay không hợp thì đổi sang giọng dự phòng và chạy lại macro. Giọng nào đọc tốt thì thêm vào danh mục với ghi chú: `voice_catalog.py add <id> "<tên>" --language vi --gender … --note "đã dùng tốt cho video …"`.

## Gợi ý theo loại video

| Loại video | Giới tính / tuổi | use_case | Từ khóa | Tốc độ |
|---|---|---|---|---|
| Đạo lý, triết lý, chữa lành | nam trung niên (hoặc nữ trung niên) | narrative_story | deep, warm, calm, wise | 0.9–0.95 |
| Cổ tích, thiếu nhi | nữ trẻ hoặc trung niên | narrative_story, characters_animation | warm, gentle, storyteller, kids | 0.95 |
| Kinh dị, bí ẩn | nam trung niên hoặc già | narrative_story | deep, dark, mysterious | 0.9 |
| Hoạt hình hài, nhân vật | theo nhân vật | characters_animation | playful, cartoon, funny | 1.0–1.1 |
| Review sản phẩm, KOC, bán hàng | theo đối tượng sản phẩm; trẻ | social_media, advertisement, conversational | energetic, friendly, upbeat | 1.05–1.15 |
| Quảng cáo cao cấp, TVC | trung niên | advertisement | confident, smooth, premium | 0.95–1.0 |
| Mẹo vặt, hướng dẫn, giáo dục | trẻ, rõ ràng | informative_educational, conversational | clear, friendly | 1.0–1.1 |
| Tin tức, tài chính | trung niên | informative_educational | neutral, professional | 1.0 |
| Thể thao, game, hype | nam trẻ | social_media, entertainment_tv | energetic, hype | 1.1 |

- Vùng miền: nội dung hoặc khán giả miền Nam thì dùng `--accent southern`; giọng Bắc thì `northern`.
- Video có nhân vật hoạt hình mà người kể là chính nhân vật đó: chọn theo tuổi và tính cách nhân vật trong `subjects`.

## Danh mục (`voices/catalog.json`)
- **Có `ELEVENLABS_API_KEY`**: `update` tải **toàn bộ** thư viện giọng ElevenLabs, mọi ngôn ngữ. Nên chạy lại mỗi tháng.
- **Chưa có key**: `update` chỉ lấy được mẫu công khai, khoảng 200 giọng. Gồm giọng mặc định của ElevenLabs, các giọng nổi bật theo từng ngôn ngữ và mục đích, cộng các giọng đã dùng trong tool. Lý do là ElevenLabs chỉ trả 3 giọng mỗi lần và không cho lọc khi chưa đăng nhập.
- Dung lượng chỉ là chữ, khoảng 1 KB mỗi giọng.
