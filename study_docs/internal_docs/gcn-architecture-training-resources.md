# GCN (Graphics Core Next) Architecture Training Resources

> **Source URL:** https://amd.atlassian.net/wiki/spaces/MLSE/pages/744166024/GCN+Graphics+Core+Next+Architecture+Training+Resources
> **pageId:** `744166024`
> **Space:** MLSE (Machine Learning Software Engineering)
> **Version:** 50 (last updated 2021-05-21)
> **Author/Owner:** Joe Greathouse
> **Fetched on:** 2026-06-26 (via Atlassian Confluence MCP, `contentFormat=markdown`)
>
> This is the full content of the internal Confluence page. The external resources
> linked below (Microsoft Stream videos, SharePoint slides/whitepapers, p4web docs,
> youtube, gpuopen PDFs, Teams) live outside Confluence and are **not** fetchable via
> the MCP — only their URLs are preserved here.

---

Previous presentations:

* **The first presentation in this series (from March 31): GPU Overview and Scheduling Kernels**

    * Stream: [https://web.microsoftstream.com/video/6b3424a4-5197-447e-9e69-96656982b36d](https://web.microsoftstream.com/video/6b3424a4-5197-447e-9e69-96656982b36d)
    * Offline Video: [https://amdcloud-my.sharepoint.com/:v:/g/personal/jgreatho_amd_com/ESTApON_HYZNmiNkQBhGDB0BhabkYfDpSRbIkPEudIuZKA](https://amdcloud-my.sharepoint.com/:v:/g/personal/jgreatho_amd_com/ESTApON_HYZNmiNkQBhGDB0BhabkYfDpSRbIkPEudIuZKA?e=MXO2zA)
    * Slides: [https://amdcloud-my.sharepoint.com/:p:/g/personal/jgreatho_amd_com/EU_aopm9G_FHqkrAu7bAFwEBuFeCg13Zw5GOBCzpZyRIeQ](https://amdcloud-my.sharepoint.com/:p:/g/personal/jgreatho_amd_com/EU_aopm9G_FHqkrAu7bAFwEBuFeCg13Zw5GOBCzpZyRIeQ?e=PX6lSb)

* **Second presentation in this series (from April 7): Scheduling Kernels**

    * Stream: [https://web.microsoftstream.com/video/82ad7631-3fe7-4100-9f4c-b6913a91492c](https://web.microsoftstream.com/video/82ad7631-3fe7-4100-9f4c-b6913a91492c)
    * Offline Video: [https://amdcloud-my.sharepoint.com/:v:/g/personal/jgreatho_amd_com/EY2xsY-M_qtCrgxh7k0WcbcBSAVk-dL8SeXxax1Yr_89-g](https://amdcloud-my.sharepoint.com/:v:/g/personal/jgreatho_amd_com/EY2xsY-M_qtCrgxh7k0WcbcBSAVk-dL8SeXxax1Yr_89-g?e=JeIQpS)
    * Slides: [https://amdcloud-my.sharepoint.com/:p:/g/personal/jgreatho_amd_com/EY-0HdmM1JJLsiyZSKTHB5wB1YJjGPBS5eORoGWGjcnXtQ](https://amdcloud-my.sharepoint.com/:p:/g/personal/jgreatho_amd_com/EY-0HdmM1JJLsiyZSKTHB5wB1YJjGPBS5eORoGWGjcnXtQ?e=0bNPsb)

* **Third presentation in this series (from April 14): Memory, IO, and CU Architecture on gfx9 GPUs**

    * Stream: [https://web.microsoftstream.com/video/6dcd95e8-626e-4c20-bc4b-c6c19685ed69](https://web.microsoftstream.com/video/6dcd95e8-626e-4c20-bc4b-c6c19685ed69)
    * Offline Video: [https://amdcloud-my.sharepoint.com/:v:/g/personal/jgreatho_amd_com/ESWmvonz2RRBqRCf1xKsCjAB-keGwezPiJut0nFgx5leSg](https://amdcloud-my.sharepoint.com/:v:/g/personal/jgreatho_amd_com/ESWmvonz2RRBqRCf1xKsCjAB-keGwezPiJut0nFgx5leSg?e=LyGz4V)
    * Slides: [https://amdcloud-my.sharepoint.com/:p:/g/personal/jgreatho_amd_com/EUe9ooGweCtHlRKBQqK_B3wBs0wU7cx6h9q7WICWzpT8IQ](https://amdcloud-my.sharepoint.com/:p:/g/personal/jgreatho_amd_com/EUe9ooGweCtHlRKBQqK_B3wBs0wU7cx6h9q7WICWzpT8IQ?e=wfQCMF)

* **Fourth presentation in this series (from April 21): Overview of AMD's gfx9 Product Portfolio and Roadmap**

    * Stream: [https://web.microsoftstream.com/video/e7820dcb-df3e-4a42-86b3-079ed0631c30](https://web.microsoftstream.com/video/e7820dcb-df3e-4a42-86b3-079ed0631c30)
    * Offline Video: [https://amdcloud-my.sharepoint.com/:v:/g/personal/jgreatho_amd_com/EU6CAMdMlPRHsxcqC2Iy5MsBYlV2V0dmtUSPKtl2L043tA](https://amdcloud-my.sharepoint.com/:v:/g/personal/jgreatho_amd_com/EU6CAMdMlPRHsxcqC2Iy5MsBYlV2V0dmtUSPKtl2L043tA?e=kvB0dB)
    * Slides: [https://amdcloud-my.sharepoint.com/:p:/g/personal/jgreatho_amd_com/EVHlgudRKCBNhFie4lchl9cBTfBvCzZvn2DU3KSd3jb2GQ](https://amdcloud-my.sharepoint.com/:p:/g/personal/jgreatho_amd_com/EVHlgudRKCBNhFie4lchl9cBTfBvCzZvn2DU3KSd3jb2GQ?e=guDg8e)

* **Fifth presentation in this series (from May 12): Compiling for gfx9**

    * Stream: [https://web.microsoftstream.com/video/b4c61390-687e-46ec-9024-99f71a178f5b](https://web.microsoftstream.com/video/b4c61390-687e-46ec-9024-99f71a178f5b?list=studio)
    * Offline Video: [https://amdcloud-my.sharepoint.com/:v:/g/personal/avoicu_amd_com/Ef4uDp-rZ_dLi_Fra3V-Ud4BEP_b5-BJMFr0xsvC-hJwRg](https://amdcloud-my.sharepoint.com/:v:/g/personal/avoicu_amd_com/Ef4uDp-rZ_dLi_Fra3V-Ud4BEP_b5-BJMFr0xsvC-hJwRg?e=pzbEiH)
    * Slides: [https://amdcloud-my.sharepoint.com/:b:/g/personal/avoicu_amd_com/ESkB5vb4vllDmSXmFpIyRzYBPlrbeqSmANWLVsVsMEY7Bg](https://amdcloud-my.sharepoint.com/:b:/g/personal/avoicu_amd_com/ESkB5vb4vllDmSXmFpIyRzYBPlrbeqSmANWLVsVsMEY7Bg?e=XkeX3G)

* **Sixth presentation in this series (from May 19): HIP Programming Course**

    * Stream: [https://web.microsoftstream.com/video/80d7c859-b850-4cd7-bda7-1fde6ed9bf51](https://web.microsoftstream.com/video/80d7c859-b850-4cd7-bda7-1fde6ed9bf51)
    * Offline Video: [https://amdcloud-my.sharepoint.com/:v:/g/personal/dancyca2_amd_com/EdUxchw8iRBCg51mnoF3h6wBYpBrfAliBtTu7xg2x2ewVA?e=dOe7Jy](https://amdcloud-my.sharepoint.com/:v:/g/personal/dancyca2_amd_com/EdUxchw8iRBCg51mnoF3h6wBYpBrfAliBtTu7xg2x2ewVA?e=dOe7Jy)
    * Slides: [https://amdcloud-my.sharepoint.com/:p:/g/personal/dancyca2_amd_com/EZlGoSwdcDBGkrKANouL1IsBc37ogOie9g4i-l-HhR57gw?e=qVfcua](https://amdcloud-my.sharepoint.com/:p:/g/personal/dancyca2_amd_com/EZlGoSwdcDBGkrKANouL1IsBc37ogOie9g4i-l-HhR57gw?e=qVfcua)

* **Seventh presentation in this series (from May 26): ML Applications and Platforms**

    * Stream: [https://web.microsoftstream.com/video/6354acff-fada-429f-944b-0e5a2e118434](https://web.microsoftstream.com/video/6354acff-fada-429f-944b-0e5a2e118434)
    * Offline Video: [https://amdcloud-my.sharepoint.com/:v:/g/personal/jgreatho_amd_com/EbIlB4gUi4tDtmMhBMdWgmIBP3W1vpxVRzcAwHErgN1Fsg?e=c6Ho6S](https://amdcloud-my.sharepoint.com/:v:/g/personal/jgreatho_amd_com/EbIlB4gUi4tDtmMhBMdWgmIBP3W1vpxVRzcAwHErgN1Fsg?e=c6Ho6S)
    * Slides: The following slides are available:

        * **ML Applications and Frameworks:** [https://amdcloud-my.sharepoint.com/:p:/g/personal/adaml_amd_com/EQKIazqVrTJBhh2nN4Hf8ccBEff6zji9FqqS1fV8VY_4uA?e=o4LMZP](https://amdcloud-my.sharepoint.com/:p:/g/personal/adaml_amd_com/EQKIazqVrTJBhh2nN4Hf8ccBEff6zji9FqqS1fV8VY_4uA?e=o4LMZP)
        * **TensorFlow / XLA / MLIR:** [https://amdcloud-my.sharepoint.com/:p:/g/personal/whchung_amd_com/EaMvj9T0e35Or3HsWKzaw7IBkcgHLOdHtQ4fwYdPEM2NbQ?e=X3R6Oy](https://amdcloud-my.sharepoint.com/:p:/g/personal/whchung_amd_com/EaMvj9T0e35Or3HsWKzaw7IBkcgHLOdHtQ4fwYdPEM2NbQ?e=X3R6Oy)

* **Eighth presentation in this series (from June 2): OpenMP**

    * Stream: [https://web.microsoftstream.com/video/4a60dd66-5fec-4e87-b6d6-b456befb4c6d](https://web.microsoftstream.com/video/4a60dd66-5fec-4e87-b6d6-b456befb4c6d)
    * Offline Video: [https://amdcloud-my.sharepoint.com/:v:/g/personal/jgreatho_amd_com/EYGKtiviC7BOmBBldrexG0MBmBVuVMeCWmx8Pkg8cUK44g?e=1FxBi2](https://amdcloud-my.sharepoint.com/:v:/g/personal/jgreatho_amd_com/EYGKtiviC7BOmBBldrexG0MBmBVuVMeCWmx8Pkg8cUK44g?e=1FxBi2)
    * Slides: [https://amdcloud-my.sharepoint.com/:p:/g/personal/jgreatho_amd_com/EdI9Lz44f2tHr9iJtU_FKaYBZs0YqSNfA-DdwJmbtSEeag?e=zWgAZI](https://amdcloud-my.sharepoint.com/:p:/g/personal/jgreatho_amd_com/EdI9Lz44f2tHr9iJtU_FKaYBZs0YqSNfA-DdwJmbtSEeag?e=zWgAZI)

* **Ninth presentation in this series (from June 9): HIP Programming Course - Advanced**

    * Stream: [https://web.microsoftstream.com/video/16f1907b-b178-48ab-82bc-0eb234f52c06](https://web.microsoftstream.com/video/16f1907b-b178-48ab-82bc-0eb234f52c06)
    * Offline Video: [https://amdcloud-my.sharepoint.com/:v:/g/personal/dancyca2_amd_com/EVHxuwwgqq1GnZZUklEpFpYB7-3TVgI_y6Qt8vwpa4xf1w?e=4QugOJ](https://amdcloud-my.sharepoint.com/:v:/g/personal/dancyca2_amd_com/EVHxuwwgqq1GnZZUklEpFpYB7-3TVgI_y6Qt8vwpa4xf1w?e=4QugOJ)
    * Slides: [https://amdcloud-my.sharepoint.com/:p:/g/personal/dancyca2_amd_com/EbqTgtJMbElOp-wPV6s3G-EB7q-aPZ1yoT2KoUw6OMGmZg?e=dMO2P5](https://amdcloud-my.sharepoint.com/:p:/g/personal/dancyca2_amd_com/EbqTgtJMbElOp-wPV6s3G-EB7q-aPZ1yoT2KoUw6OMGmZg?e=dMO2P5)

‌

# Hardware Description Presentations

* **AMD GPUVM for ROCm v1.3** – Joe Greathouse

    * slides: [https://amdcloud-my.sharepoint.com/:p:/g/personal/jgreatho_amd_com/EXi96pb0cTZIpe0HwsHWgBIB5kCu0ZQdHMO9YEv1qkYUzQ?e=H0xjpu](https://amdcloud-my.sharepoint.com/:p:/g/personal/jgreatho_amd_com/EXi96pb0cTZIpe0HwsHWgBIB5kCu0ZQdHMO9YEv1qkYUzQ?e=H0xjpu)

‌

If you are in MLSE, you can get access to the offline videos and slides from here as well: [https://amdcloud.sharepoint.com/:f:/r/sites/mlse/Shared%20Documents/Internal%20-%20MLSE%20All/Training/GCN%20Training%20(5%20parts)](https://amdcloud.sharepoint.com/:f:/r/sites/mlse/Shared%20Documents/Internal%20-%20MLSE%20All/Training/GCN%20Training%20(5%20parts)?csf=1&web=1&e=y0Ca6A)

‌

Thanks,

\-Joe

P.S.

And if you have not received it yet, this is the background info that we sent out before the first talk:

**Attendees should be familiar with the basics of programming GPUs in HIP, OpenCL, CUDA, or others such GPU compute languages.** Recommended viewing or reading about this:

* Introduction to AMD GPU programming with HIP Webinar: [https://www.youtube.com/watch?v=3ZXbRJVvgJs](https://www.youtube.com/watch?v=3ZXbRJVvgJs)
* Various HIP guides:

    * [https://github.com/ROCm-Developer-Tools/HIP/blob/master/docs/markdown/hip_porting_guide.md](https://github.com/ROCm-Developer-Tools/HIP/blob/master/docs/markdown/hip_porting_guide.md)
    * [https://github.com/ROCm-Developer-Tools/HIP/blob/master/docs/markdown/hip_programming_guide.md](https://github.com/ROCm-Developer-Tools/HIP/blob/master/docs/markdown/hip_programming_guide.md)
    * [https://github.com/ROCm-Developer-Tools/HIP/blob/master/docs/markdown/hip_terms.md](https://github.com/ROCm-Developer-Tools/HIP/blob/master/docs/markdown/hip_terms.md)
    * [https://github.com/ROCm-Developer-Tools/HIP/blob/master/docs/markdown/hip_kernel_language.md](https://github.com/ROCm-Developer-Tools/HIP/blob/master/docs/markdown/hip_kernel_language.md)
    * [https://github.com/ROCm-Developer-Tools/HIP/blob/master/docs/markdown/hip_faq.md](https://github.com/ROCm-Developer-Tools/HIP/blob/master/docs/markdown/hip_faq.md)
    * [https://gpuopen.com/hip-to-be-squared-an-introductory-hip-tutorial/](https://gpuopen.com/hip-to-be-squared-an-introductory-hip-tutorial/)

‌

**Attendees may want to familiarize themselves with the basics of AMD's GCN/CDNA Architecture.** Recommended viewing or reading about this:

* AMD-provided introductions to GCN1 (from 2011 and 2012). Some things will be out of date:

    * AMD Graphics Core Next Presentation: [http://developer.amd.com/wordpress/media/2013/06/2620_final.pdf](http://developer.amd.com/wordpress/media/2013/06/2620_final.pdf)
    * AMD Graphics Core Next (GCN) Architecture White Paper: [https://amdcloud-my.sharepoint.com/:b:/g/personal/jgreatho_amd_com/EUYOx_wIGW5Is4VbULXebzkBrR2B14N_no6Xlrx9bljizQ?e=qOSXiW](https://amdcloud-my.sharepoint.com/:b:/g/personal/jgreatho_amd_com/EUYOx_wIGW5Is4VbULXebzkBrR2B14N_no6Xlrx9bljizQ?e=qOSXiW)

* Introduction to Vega 10: [https://www.hotchips.org/wp-content/uploads/hc_archives/hc29/HC29.21-Monday-Pub/HC29.21.10-GPU-Gaming-Pub/HC29.21.120-Radeon-Vega10-Mantor-AMD-f1.pdf](https://www.hotchips.org/wp-content/uploads/hc_archives/hc29/HC29.21-Monday-Pub/HC29.21.10-GPU-Gaming-Pub/HC29.21.120-Radeon-Vega10-Mantor-AMD-f1.pdf)
* Gfx9 Overview document: [http://p4web.amd.com:1677/@md=d&cd=//&cdf=//gfxip/gfx9/doc/design/architecture/GFX9_TopLevel_Arch_Short_V2.docx&c=f56@//gfxip/gfx9/doc/design/architecture/GFX9_TopLevel_Arch_Short_V2.docx?ac=22](http://p4web.amd.com:1677/@md=d&cd=/&cdf=/gfxip/gfx9/doc/design/architecture/GFX9_TopLevel_Arch_Short_V2.docx&c=f56@/gfxip/gfx9/doc/design/architecture/GFX9_TopLevel_Arch_Short_V2.docx?ac=22)

**Further information for interested attendees: deep-dive details.**

* Layla Mah's GCN Crash Course: [https://amdcloud-my.sharepoint.com/:p:/g/personal/jgreatho_amd_com/EfkN58BwWtVFpc2gm9X12isBIjC11J-28kxf-8j8oPClSw?e=VDaM8h](https://amdcloud-my.sharepoint.com/:p:/g/personal/jgreatho_amd_com/EfkN58BwWtVFpc2gm9X12isBIjC11J-28kxf-8j8oPClSw?e=VDaM8h)
* Internal ISA guide for our gfx9 GPUs: [http://p4web.amd.com:1677/@md=d&cd=//&cdf=//gfxip/gfx9/doc/design/blocks/sq/arch/Gfx9_Shader_Programming.docx&c=l4z@//gfxip/gfx9/doc/design/blocks/sq/arch/Gfx9_Shader_Programming.docx?ac=22](http://p4web.amd.com:1677/@md=d&cd=/&cdf=/gfxip/gfx9/doc/design/blocks/sq/arch/Gfx9_Shader_Programming.docx&c=l4z@/gfxip/gfx9/doc/design/blocks/sq/arch/Gfx9_Shader_Programming.docx?ac=22)
* Timothy Lotte's Advanced Shader Programming on GCN: [https://gpuopen.com/wp-content/uploads/2017/03/GDC2017-Advanced-Shader-Programming-On-GCN.pdf](https://gpuopen.com/wp-content/uploads/2017/03/GDC2017-Advanced-Shader-Programming-On-GCN.pdf)

‌

**And for anyone who wants to know how our GPUs are used for graphics:**

[https://teams.microsoft.com/l/team/19%3a62201fa0a7144f839c4f050b53095c20%40thread.skype/conversations?groupId=3410682c-b5b9-4fbe-9596-b0d5b5ac54b4&tenantId=3dd8961f-e488-4e60-8e11-a82d994e183d](https://teams.microsoft.com/l/team/19%3a62201fa0a7144f839c4f050b53095c20%40thread.skype/conversations?groupId=3410682c-b5b9-4fbe-9596-b0d5b5ac54b4&tenantId=3dd8961f-e488-4e60-8e11-a82d994e183d)

* In particular, for compute users:

    * "Hardware Level of the Graphics Pipeline" – This is _for graphics_ and _not all parts of this talk are true for compute_, but the first 36 minutes may be useful (up through "SX").
    * "Hardware Execution of Shaders" – Minutes 9-12 may be useful for compute users. Same for minute 59-67, 79-85.
