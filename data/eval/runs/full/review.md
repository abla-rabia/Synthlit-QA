# Relecture manuelle

Pour chaque réponse : compte les affirmations (claims_total) et combien sont bien dans les passages cités (claims_supported), puis écris les deux nombres dans manual.csv.

Réglages du run : `{"multiquery": true, "hybrid": true, "rerank": true}`

---

## q01 · factuelle
**Question :** How many patients were included in the Zimmermann study and what tumour type did they have?

**Gold :** 
- 2022_zimmermann_mri-sequence-independent-head-sct-proton | Abstract | pp. 1-1

**Réponse de référence :** 47 meningioma patients (33 training, 6 validation, 8 test), all treated with proton therapy.

**Retrouvé :** top10 1/1 · top5 0/1

**Réponse du système :**

47 patients, all with meningioma. [1]

> **[1] 2022_zimmermann_mri-sequence-independent-head-sct-proton** · 2 Materials and methods · p. 2-3
> In total 47 meningioma patients treated with proton therapy were included in this study. All patients received MR (Inge-nia 3.0, Philips, Netherlands) and CT (Big Bore CT, Philips, Netherlands) scans on the same day in treatment position using immobilisation devices, like thermoplastic face masks and necessary positioning tools administered during proton irradiation. In more detail the model was trained with data from 33 patients, six patients were used for validation, and eight for testing the model. All patients were included in a prospective clinical study at the MedAustron Center for Ion Beam Therapy and Research [18], approved by the responsible ethics commit-tee (Niederösterreische Ethikkommission, Austria) under the number GS1-EK-4/350-2015. The CT sequence was acquired with a peak voltage of 120 kV. The volume was reconstructed with a transversal plane resolution of 0.684 × 0.684 mm2 and a slice thickness of 2 mm. For the CT protocol the HU calibration was acquired and validated at the MedAustron Center for Ion Therapy and Research during the commissioning phase using the CIRS electron density phantom (CIRS, Norfolk, US). Used MR sequence parameters. Contrast agent No No Yes MRI included T2- and T1-weighted sequences, where T1-weighted was performed with and without contrast medium (CM). Image resolution and slice thickness varied for different sequences between 0.2 × 0 …

---

## q02 · article
**Question :** Which databases and period did the Dayarathna review search?

**Gold :** 
- 2024_dayarathna_mri-ct-pet-review | 1. Introduction | pp. 2-2

**Réponse de référence :** Scopus and PubMed, 2018 to July 2023 (with Google Scholar complement).

**Retrouvé :** top10 1/1 · top5 1/1

**Réponse du système :**

The review searched the Scopus and PubMed databases for articles published from 2018 up to July 2023 [1].

> **[1] 2024_dayarathna_mri-ct-pet-review** · 1. Introduction · p. 2-2
> • This review further identifies challenges and limitations in the current methods and discusses the possible future directions in medical image synthesis. Search Criteria: We conducted a literature search using Scopus and PubMed databases to find relevant articles published from 2018 to 2023 July with the search term (‘‘synth*’’ OR ‘‘pseudo’’ OR ‘‘translat*’’) AND ‘‘deep learning’’ AND (‘‘medical imag*’’ OR ‘‘CT’’ OR ‘‘MRI’’ OR ‘‘MR’’ OR ‘‘PET’’ OR ‘‘low dose’’ OR ‘‘low count’’ OR ‘‘low field’’) in the title, abstract or keywords. Google Scholar was also used to identify possible omissions and excluded the review articles. We first screened titles and abstracts, considering inclusion criteria such as peer-reviewed journals and conference papers and excluding irrelevant topics such as image translation for super-resolution and reconstruction. After a full document review and cross-referencing,173 articles were included. Fig. 2 illustrates the methodological process followed in the literature review search flow. Paper Organization: The schematic representation of this manu-script’s layout can be found in Fig. 3. Section 2 provides an overview of synthetic image contrasts and deep learning-based networks in medical image synthesis. Section 3 presents a review of various deep learning-based medical image synthesis methods. Section 4 analyses the network architectures and their app …

---

## q03 · synthese
**Question :** What are common ways of using U-Net for medical image synthesis?

**Gold :** 
- 2024_dayarathna_mri-ct-pet-review | 2.1.1. U-Nets | pp. 3-3

**Réponse de référence :** U-Net used as cGAN generator, base encoder-decoder, and 3D variant (Zimmermann).

**Retrouvé :** top10 0/1 · top5 0/1

**Réponse du système :**

Common approaches for employing U‑Net in medical image synthesis include:  

1. **Standalone encoder‑decoder synthesis** – U‑Net is used directly as a generator that maps a source modality to a target modality, preserving spatial resolution through skip connections. This is the standard “U‑Net” or “nnU‑Net” architecture used for CT‑from‑CBCT, MRI‑to‑CT, and other cross‑modality tasks. [3]  

2. **U‑Net within GAN frameworks** – The U‑Net encoder‑decoder is combined with a discriminator in conditional GANs (cGANs) or CycleGANs to improve realism and enforce adversarial constraints. The U‑Net generator is often called U‑cGAN. [2]  

3. **Modified U‑Net variants** – Enhancements such as residual blocks (residual U‑Net), attention mechanisms (Attention U‑Net), dropout layers, and alternative final activations (tanh instead of sigmoid for regression) are added to improve generalization, reduce over‑fitting, and better capture global context. These variants are applied in multi‑contrast MRI translation and other synthesis tasks. [3], [5]  

4. **Multi‑scale and multi‑contrast extensions** – U‑Net is adapted to process multiple input contrasts (MISO/MIMO) or to fuse features at different spatial scales, enabling synthesis of one contrast from several others or of high‑resolution images from low‑resolution inputs. [1]  

These strategies illustrate how U‑Net serves as a flexible backbone for both pure synthesis and adversarially‑augmented medical image generation.

> **[3] 2025_guo_ct-synthesis-radiotherapy-review** · 3. Deep Learning Models · p. 4-5
> CNNs have been applied in many sCT generation frameworks across both CBCT- and MRI-based modalities [30–36]. Among them, U-Net [37] and its variants have been the most widely adopted architectures. As depicted in Figure 1, due to the encoder–decoder structure and the inclusion of skip connections, U-Net models enable the preservation of spatial resolution and contextual information of the input modality throughout the network [38]. The nnU-Net (no-new U-Net) [39], a widely recognized framework for medical image segmentation, has also been adapted for MRI-to-CT synthesis [40]. To further enhance structural consistency, several modifications to the standard U-Net have been proposed. For instance, residual U-Net integrates residual blocks to mitigate vanishing gradients and facilitate deeper architectures [41]. Attention U-Net incorporates a self-attention scheme along the skip pathways to learn important features [42]. While CNNs are effective at learning local features, they may struggle to capture relationships between far-apart regions, which has led to interest in architectures such as transformers [14]. Figure 1. Overview of UNet-based CT synthesis from CBCT. The blue box stands for convolutional blocks, and the arrow represents the data flow from the encoder to the de-coder (flow of features).

> **[2] 2021_baydoun_pelvis-sct-cervical-single-input-gan** · C. U-NET · p. 6-6
> A u t h o r M a n u s c r i p t u t h o r M a n u s c r i p t A u t h o r M a n u s c r i p t synthesis using a convolutional capsule GAN while implementing a U-Net generator with the traditional encoder/decoder depth of 3 [37]. Using a similar generator to that of Bass et al. [37], Ben-Cohen et al. were able to generate synthetic Positron Emission Tomography (PET) images from measured CT in a cGAN framework [38]. In the rest of this manuscript, we will use the model adopted by Ben-Cohen et al. as a benchmark for comparison and will refer to this model as U-cGAN. In our current application, the number of trainable parameters for U-cGAN is 4,868,614. Our group introduced, for semantic segmentation, the sU-Net concept with an encoder/ decoder depth of 2 [21]. Compared to the commonly used U-Net, sU-Net tends avoid unnecessary complexity by limiting the number of parameters to be optimized, avoiding the vanishing gradient effect, and requiring less training data. When supplemented by general anatomical topography knowledge, sU-Net performed accurate and rapid image segmentation for five structures on T2-weighted, TSE-SSH MR images of patients with cervical cancer [21]. Herein we propose the first use of the sU-Net model for image synthesis.

> **[5] 2022_osman_brain-mri-intramodality-synthesis** · 1 Department of Medical Physics,Al-Neelain University,Khartoum 11121,Sudan · p. 2-2
> Dai et al.21 studied a unified-GAN model for image-to-image translation across four MRI sequences. Despite the promising reported results, there is still a need for exploring other methods with improved generalizability for image-to-image translation across different MR sequences. U-Net architecture, a class of deep learning algorithms that belongs to the fully CNNs, has been used as a standard for semantic image segmentation where it showed outstanding performance.5 Its training pro-cedure is efficient when using limited computational resources compared with GANs.Moreover,it can derive local and global features from the input images to generate pixel/voxel-wise predictions. Inspired by its success in the image segmentation task,we studied an end-to-end deep learning convolutional U-Net model for image-to-image translations across three standards MRI contrasts for the brain using a relatively large-scale open-source dataset from multiple institutions. Among the existing MR contrasts, each image contrast can be translated to the rest contrasts using the appropriate model. This is clinically helpful in situations where multiple MRI contrasts are needed for diagnosis and treatment planning, but only one MRI contrast could be practically acquired. We also compared our results with those achieved with state-of-the-art models in the liter-ature that utilized the same dataset.Our end- …

> **[1] 2024_dayarathna_mri-ct-pet-review** · 4. Analysis of networks · p. 13-14
> Deep-learning-based architectures predominantly employed in medical image synthesis include CNN networks, U-Nets, GAN-based networks, Transformer-based networks and, more recently, Diffusion-based architectures. CNNs gained popularity due to their exceptional performance in computer vision tasks, particularly in medical imaging. These techniques (Chartsias et al., 2018; Fu et al., 2019; Lin et al., 2019; Florkow et al., 2020; Sanaat et al., 2020; Hussein et al., 2022) have demonstrated their ability to synthesize images in a target domain from a distinct source domain and generate high-resolution images from low-resolution counterparts. The literature reveals that cGANs and CycleGANs have been most extensively utilized for synthetic MR and pseudo-CT generation. In contrast, cGANs and U-Nets have been commonly employed for synthetic PET synthesis. Moreover, there has been a notable increase in interest towards transformer and Diffusion-based architectures for medical image synthesis. The literature’s deep neural networks for medical image synthesis can be clustered based on their architecture types to support different input and feature-level enhancements. As shown in Fig. 12 multi-contrast networks include Single Input Multiple Output (SIMO), Multiple Input Single Output (MISO), and Multiple Input Multiple Output (MIMO) networks for image synthesis. Further, Multi-scale archite …

---

## q04 · croisement
**Question :** Which indexed papers address CBCT-to-CT synthesis, and which network types do they use?

**Gold :** 
- 2021_rossi_cbct-sct-supervised-vs-unsupervised | 2.3. Deep Convolutional Neural Network Models | pp. 4-5
- 2022_yoo_cbct-sct-feature-driven-loss | 2.2. Loss Functions on FC DensNet | pp. 3-4
- 2023_suwanraksa_cbct-ct-registration-gan-head-neck | 2.4. Pix2Pix | pp. 9-9
- 2023_liu_cbct-ct-cervical-unet-hybrid-dataset | 2.2. Network Architecture | pp. 6-6
- 2023_szmul_cbct-sct-abdominal-paediatric | 2.1.3. Design of the cycleGAN network | pp. 5-5
- 2024_pepa_cbct-sct-unsupervised-paediatric-proton-carbon | 2.5. CycleGAN | pp. 6-7

**Réponse de référence :** Rossi 2021 (U-Net vs CycleGAN), Yoo 2022 (FC-DenseNet), Suwanraksa 2023 (Pix2Pix/CycleGAN/UNIT + RegNet), Liu 2023 (residual U-Net hierarchical), Szmul 2023 (CycleGAN + global residuals), Pepa 2024 (CycleGAN Res-Net/U-Net).

**Retrouvé :** top10 0/6 · top5 0/6

**Réponse du système :**

**CBCT‑to‑CT synthesis papers (from the indexed collection)**  

| Paper | Network type(s) reported in the passage |
|-------|----------------------------------------|
| Suwanraksa et al., 2023 | U‑Net and generative adversarial networks (GANs) in general; the passage notes that “many models have been proposed … with the most popular being U‑Net and generative adversarial networks” [2]. |
| Pepa et al., 2024 | CycleGAN with 2‑D CycleGAN architectures featuring Res‑Net and U‑Net generators [4]. |
| Molina‑Maza et al., 2025 | CBCT‑based CT synthesis is discussed, but the passage does not specify a particular network architecture [5]. |

These are the indexed papers that explicitly address CBCT‑to‑CT synthesis in the provided passages and the network types they employ.

> **[2] 2023_suwanraksa_cbct-ct-registration-gan-head-neck** · 1. Introduction · p. 3-3
> There has been a growing interest in using deep learning to generate sCT from CBCT. This is partly due to the increasing availability of high-performance computational resources over the last decade which has enabled the training of a large number of images, allowing fast image translation within a few milliseconds. Compared with traditional approaches, the use of deep learning to convert CBCT to sCT has resulted in significant improvements in image quality and speed. Ideally, sCT generated from CBCT should have CT numbers as accurate as pCT while maintaining anatomical accuracy similar to CBCT. In general, medical image synthesis can be described as an image-to-image translation problem in which a model maps the source image (A) to the target image (B) [24]. Many models have been proposed for image-to-image translation, with the most popular being U-Net [25] and generative adversarial networks (GANs) [26]. U-Net is a U-shaped sym-metric encoder-decoder architecture designed primarily for semantic segmentation. The encoder acts as a feature extractor and learns an abstract representation of the source image, whereas the decoder translates the feature representation into the target image. A GAN is a framework consisting of a deep generative model and a discriminative model through an adversarial process. The generator converts the source image into the target image, whereas the  …

> **[4] 2024_pepa_cbct-sct-unsupervised-paediatric-proton-carbon** · 1. Introduction · p. 2-3
> In the context of medical image synthesis, several DL-based architectures for enhancing CBCT image quality were reported [37]. Among them, cycle consistency GAN (CycleGAN) has gained popularity as it allows us to use unpaired data for training, which is particularly important when CBCT and CT image pairs with completely matching anatomy are not available [17,23,24,38–42]. Despite the undisputable advances in the field, relevant open challenges still remain that prevent the routine use of DL and CycleGANs for image translation tasks in clinical settings and APT workflows [8]. In this work, we propose and evaluate a hybrid analytical and DL-based framework for CBCT to CT image synthesis tailored on a population of paediatric patients and young adults towards the implementation of APT pathways. In particular, this study focuses on an analytical ring artefact correction method followed by the generation of sCT scans based on 2D CycleGAN architectures featuring Res-Net and U-Net generators. The validity of the generated sCT scans is assessed in terms of qualitative and quantitative image quality, reserving dosimetric evaluations for future investigations. To the best of our knowledge, this study represents the first attempt to generate and evaluate DL-based sCT from narrow field-of-view (FOV) CBCT in a population of paediatric patients treated with either protons or carbon ions.

> **[5] 2025_molina-maza_cbct-mri-sct-proton-head** · 2 STATE-OF-THE-ART · p. 3-3
> Indeed, the present work represents a notable nov-elty within the current state-of-the-art on DL techniques for CBCT-based CT synthesis in APT, and it poses a significant contribution to the medical physics community. Originally, our initial retrospective dataset comprised 60 patients.However,we needed to specifically collect three different types of images for each patient: a specific T1 MRI sequence, a CBCT, and a CT scan. Since PT is a relatively novel technique and we specifically focus on HC, we needed to narrow down the initial number of patients available. Thus, our final data set contains 137 triple groups of MRI-CBCT-CT volumes derived from 27 patients (average age of 30.89 ± 23.05 years,age range of 3–75 years,11 women) that were retrospectively col-lected from Centro de Protonterapia Quironsalud (CPT). Our selection criteria encompassed patients diagnosed with brain cancer and treated with PT. Head CBCT and CT scans comprised a five-day timeframe and the same immobilization, while MRI scans were acquired at the beginning of the PT treatment. CT scans were acquired with a general electric (GE) revolution CT scan-ner (General Electric Healthcare, Chicago, IL, USA): ASIR-60 iterative reconstruction, 120 kVp, pixel size = 0.625 mm, slice thickness = 1.250 mm, FOV = 50 cm, matrix size = 512 × 512, metal artifact reduction filters. Besides, in-room CBCT scans were performe …

---

## q05 · definition
**Question :** What is the difference between MRI and CT?

**Gold :** 
- 2021_rossi_cbct-sct-supervised-vs-unsupervised | 1. Introduction | pp. 1-1
- 2021_baydoun_pelvis-sct-cervical-single-input-gan | I. INTRODUCTION | pp. 2-3

**Réponse de référence :** CT = X-rays, attenuation (HU), electron density, needed for dose. MRI = magnetic field, radio waves, soft-tissue contrast, no electron density.

**Retrouvé :** top10 0/2 · top5 0/2

**Réponse du système :**

MRI and CT differ in physics, image content and clinical use.  
MRI uses a magnetic field and radio‑frequency pulses to image hydrogen nuclei, giving excellent soft‑tissue contrast and no ionizing radiation, but it does not provide electron‑density maps needed for dose calculation [1].  
CT uses X‑ray attenuation to produce images that contain electron‑density information for dose planning and bone detail, but it exposes patients to ionizing radiation and is less sensitive to soft‑tissue contrast [3].

> **[1] 2023_li_ct-from-mri-multiscale-network** · 1 Introduction · p. 1-2
> Magnetic resonance imaging (MRI) is an important medical imaging modality as it presents a clear soft-tissue structure of the human body without introducing ionizing radiations like in computed tomography (CT) [1]. Currently, MRI is widely used in clinical diagnosis and tumor or organ delineation. However, since MRI cannot reflect the electron density of the human body, CT is still essential in the current radiation therapy (RT) workflow for a dose plan [2]. For increasing the efficiency of RT and prevent additional ionizing radiation to patients, studies were carried out to investigate the possibility of using MR images to synthesize CT and replace its function in RT [3].

> **[3] 2021_wang_synthesis-review** · 3.D | Other · p. 5-6
> The fused image is then fed into the generative network in a GAN architecture.40 In contrast to common In the current radiation therapy workflow, both MR and CT imaging are frequently performed on many patients for the purpose of treatment planning (i.e., simulation). MR images feature excellent soft tissue contrast that is useful for delineation of gross tumor as well as organs at risk (OARs)42 while CT images provide electron density maps for dose calculation and reference images for pretreat-ment positioning. The contours from MR images are propagated to CT images by image registration for treatment planning. However, using both imaging modalities not only leads to additional time and cost for the patient, but also introduces systematic positioning errors during the CT‐MRI image fusion process.43–45 Moreover, CT also subjects patients to exposure to a non‐negligible dose of ionizing radiation,46 especially in those requiring resimulation. Thus, highly desirable to bypass CT scans in favor of an MRI‐based treat-it is ment planning workflow. Emerging MR‐linear accelerator (MR‐linac) technology also motivates the exclusive use of MRI in radiotherapy.47,48 Without accurate image synthesis, MR imaging cannot replace CT imaging in radiotherapy because the signal recorded in MR images derives from the hydrogen nucleus and thus cannot provide material attenuation coefficients for el …

---

## q06 · hors_sujet
**Question :** What is a good recipe for jollof rice?

**Gold :** aucun (refus attendu)

**Réponse de référence :** Refus attendu (la phrase de refus du système, pas une réponse sur le riz).

**Refus :** oui (attendu : oui)

**Réponse du système :**

I don't have enough information in the indexed papers to answer this question.
