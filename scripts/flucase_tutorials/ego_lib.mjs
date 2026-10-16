// flucase 浏览器测试的公共函数（虚构数据，测试账号）。用法：在 ego-browser 脚本里 await import("file://<本文件绝对路径>")
export const BASE = "http://127.0.0.1:8765";   // 测试服务的地址（正式模式、空数据目录）
const WORK = new URL("../../tmp/flucase_tutorial/", import.meta.url).pathname;   // BaseModel/tmp/flucase_tutorial/
export const SHOTS = decodeURIComponent(WORK) + "shots";
export const FILES = decodeURIComponent(WORK) + "files";
export const PW = "Flu-test-2026";   // 测试账号统一的虚构密码

export async function setup(page) {
  await page.cdp("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
}

export async function logout(page) {
  await page.goto(BASE + "/login");
  await page.fetch("/api/auth/logout", { method: "POST" });
}

export async function login(page, username, password = PW) {
  await setup(page);
  await logout(page);
  await page.goto(BASE + "/login");
  await page.waitForSelector("text=登录");
  await page.fill("input[autocomplete=username]", username);
  await page.fill("input[autocomplete=current-password]", password);
  await page.click("button[type=submit]", { label: "登录" });
  await page.waitForFunction(() => !location.pathname.startsWith("/login"), undefined, { timeout: 10_000 });
  await page.waitForTimeout(800);
}

export async function noAnim(page) {
  await page.evaluate(() => {
    if (document.getElementById("__noanim")) return;
    const st = document.createElement("style");
    st.id = "__noanim";
    st.textContent = "*,*::before,*::after{transition:none!important;animation-duration:0s!important;animation-delay:0s!important}";
    document.head.appendChild(st);
  });
}

export async function shot(page, name, opts = {}) {
  await noAnim(page);
  await page.waitForTimeout(opts.wait ?? 1000);
  return page.screenshot({ path: `${SHOTS}/${name}.png`, ...opts.clip ? { clip: opts.clip } : {}, ...opts.fullPage ? { fullPage: true } : {} });
}

/** 页面主区域的可见文字（不含侧栏），用于核对数字 */
export async function mainText(page) {
  return page.evaluate(() => (document.querySelector("main, .el-main") ?? document.body).innerText);
}

/** 把主内容区滚到某段文字附近 */
export async function scrollTo(page, text) {
  await page.evaluate((t) => {
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = w.nextNode())) {
      if (n.textContent.includes(t)) { n.parentElement.scrollIntoView({ block: "start" }); return true; }
    }
    return false;
  }, text);
  await page.waitForTimeout(300);
}

/** 点第 nth 个文字完全等于 text 的可见元素（按钮、链接、单选、页签…） */
export async function clickExact(page, text, nth = 0, sel = "button, a, .el-link, .el-radio-button, .el-radio, .el-tabs__item, .el-dropdown-menu__item, .el-select-dropdown__item, span, label, div") {
  const ok = await page.evaluate(({ text, nth, sel }) => {
    const els = [...document.querySelectorAll(sel)].filter(e => e.offsetParent !== null && e.innerText?.trim() === text);
    // 去掉包含另一个匹配元素的外层
    const inner = els.filter(e => !els.some(o => o !== e && e.contains(o)));
    const t = inner[nth];
    if (!t) return inner.length;
    t.scrollIntoView({ block: "center" });
    t.click();
    return true;
  }, { text, nth, sel });
  if (ok !== true) throw new Error(`clickExact: 找不到第 ${nth} 个“${text}”（共 ${ok} 个）`);
  await page.waitForTimeout(500);
}
