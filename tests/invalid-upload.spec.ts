import { test, expect } from '@playwright/test';

test('reject invalid file type', async ({ page }) => {
  await page.goto('http://localhost:8501/');

  await page
    .getByTestId('stFileUploaderDropzoneInput')
    .setInputFiles('lol.jpg');

  await expect(page.locator('body')).toContainText(
    /pdf|invalid|unsupported/i
  );
});