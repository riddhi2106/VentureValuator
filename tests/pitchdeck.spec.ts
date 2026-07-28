import { test, expect } from '@playwright/test';

test('pitch deck is generated', async ({ page }) => {
  await page.goto('http://localhost:8501/');

  await page
    .getByTestId('stFileUploaderDropzoneInput')
    .setInputFiles('Untitled document (4).pdf');

  await page.getByTestId('stBaseButton-primary').click();

  await expect(
    page.getByRole('button', {
      name: 'Download pitch deck (.pptx)'
    })
  ).toBeVisible();
});