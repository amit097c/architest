const { test, expect } = require('@playwright/test');

test('Generated Test', async ({ page }) => {
    await page.goto('https://www.demoblaze.com/');
    await step_1_clickSamsungGalaxyS6(page); // 1.  From the homepage, click "Samsung galaxy s6"
});

// async function step_1_clickSamsungGalaxyS6(page) {
//     const productLink = page.getByRole('link', { name: 'Samsung galaxy s6' });
//     await expect(productLink).toBeVisible();
//     await productLink.click();
// }

async function step_1_clickSamsungGalaxyS6(page) {
    const productLink = page.locator('a.hrefch', { hasText: 'Samsung galaxy s6' });
    await expect(productLink).toBeVisible({ timeout: 10000 });
    await productLink.click();
}
// const { test, expect } = require('@playwright/test');

// test('Generated Test', async ({ page }) => {
//     await page.goto('https://www.demoblaze.com/');
//     await step_1_clickSamsungGalaxyS6(page); // 1. From the homepage, click "Samsung galaxy s6"
// });

// async function step_1_clickSamsungGalaxyS6(page) {
//     const productLink = page.getByText('Samsung galaxy s6');
//     await expect(productLink).toBeVisible();
//     await productLink.click();
// }