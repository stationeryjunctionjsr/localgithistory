'use client';

import Script from 'next/script';

export default function MSG91Initializer() {
  // Removed duplicate useEffect initialization which causes "Widget not found"
  // MSG91 script is solely initialized through the onLoad callback of the Script tag now.

  return (
    <Script
      src="https://verify.msg91.com/otp-provider.js"
      strategy="afterInteractive"
      onLoad={() => {
        if (typeof window !== 'undefined') {
          const initFn = (window as any).initSendOTP || (window as any).initOTP;
          if (initFn) {
            const widgetId = process.env.NEXT_PUBLIC_MSG91_WIDGET_ID;
            const tokenAuth = process.env.NEXT_PUBLIC_MSG91_TOKEN_AUTH;
            if (!widgetId || !tokenAuth) {
              console.warn(
                'MSG91 widget credentials not configured. Set NEXT_PUBLIC_MSG91_WIDGET_ID and NEXT_PUBLIC_MSG91_TOKEN_AUTH.'
              );
              return;
            }
            const configuration = {
              widgetId,
              tokenAuth,
              exposeMethods: true,
              success: (data: any) => {
                if (process.env.NODE_ENV !== 'production') {
                  console.log('MSG91 Initialization Success:', data);
                }
              },
              failure: (error: any) => {
                console.error('MSG91 Initialization Failure:', error);
              },
            };
            initFn(configuration);
            if (process.env.NODE_ENV !== 'production') {
              console.log('MSG91 SDK Initialized Successfully');
            }
          } else {
            console.warn('MSG91 initialization function not found on window object.');
          }
        }
      }}
    />
  );
}
