// Site-level metadata. Fill in the arXiv / code URLs once public.
export const META = {
  title: 'Predicting Alignment Generalization with Value Representations',
  short: 'Value Generalization',
  paperUrl: null,                 // header "Paper" link, hidden until set
  arxivUrl: '#',                  // TODO: arXiv abs URL
  codeUrl: 'https://github.com/andyjliu/value-generalization',
  authors: [
    { name: 'Andy Liu', aff: [1] },
    { name: 'Mehar Bhatia', aff: [2, 3] },
    { name: 'Karolina Stańczak', aff: [4, 5] },
    { name: 'Mona Diab', aff: [1] },
    { name: 'Vered Shwartz', aff: [6, 7] },
    { name: 'Daniel Fried', aff: [1] },
  ],
  affiliations: ['Carnegie Mellon University', 'Mila - Quebec AI Institute', 'McGill University', 'ETH Zurich', 'ETH AI Center', 'University of British Columbia', 'Vector Institute'],
  bibtex: `@article{liu2026predicting,
  title   = {Predicting Alignment Generalization with Value Representations},
  author  = {Liu, Andy and Bhatia, Mehar and Sta{\\'n}czak, Karolina and Diab, Mona and Shwartz, Vered and Fried, Daniel},
  journal = {arXiv preprint},
  year    = {2026}
}`,
};

export const SECTIONS = [
  { id: 'generalization', label: 'Alignment generalization matrices' },
  { id: 'predictors', label: 'Benchmarking predictors' },
  { id: 'taxonomy', label: 'ValueMap Taxonomy' },
  { id: 'multivalue', label: 'Multi-Value Coherence' },
];
