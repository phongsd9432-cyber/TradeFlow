// Script nhỏ, không phụ thuộc thư viện nào.
// 1) Hộp xác nhận cho nút có thuộc tính data-confirm.
document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-confirm]");
  if (el && !window.confirm(el.dataset.confirm)) e.preventDefault();
});
// 2) Nút "So sánh" chỉ bật khi đã tick ít nhất 2 báo giá.
document.querySelectorAll("form[data-compare]").forEach((form) => {
  const button = form.querySelector("button[data-needs-two]");
  const boxes = form.querySelectorAll("input[name=ids]");
  const sync = () => { if (button) button.disabled = form.querySelectorAll("input[name=ids]:checked").length < 2; };
  boxes.forEach((b) => b.addEventListener("change", sync));
  sync();
});
